"""
Generates tracking events by creating test users and fake activity.

This should never be run on a production server as it will generate a lot of
bad data. It is entirely for benchmarking purposes in load test environments.
It is also fragile due to reaching into the edx-platform testing internals.
"""

import csv
import io
import json
import logging
import uuid
from datetime import datetime, timedelta
from random import choice
from textwrap import dedent
from time import sleep
from typing import Any, List

import requests
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from platform_plugin_aspects.sinks.base_sink import ClickHouseAuth

# For testing we won't be able to import from edx-platform
try:  # pragma: no cover
    from cms.djangoapps.contentstore.views.course import create_new_course_in_store
    from common.djangoapps.student.helpers import do_create_account
    from common.djangoapps.student.models.course_enrollment import CourseEnrollment
    from openedx.core.djangoapps.user_authn.views.registration_form import (
        AccountCreationForm,
    )
    from xmodule.modulestore import ModuleStoreEnum

    RUNNING_IN_PLATFORM = True
except ImportError:
    create_new_course_in_store = None
    do_create_account = None
    CourseEnrollment = None
    AccountCreationForm = None
    ModuleStoreEnum = None

    RUNNING_IN_PLATFORM = False

log = logging.getLogger("tracking_event_loadtest")


class LoadTest:
    """
    Runs the load test and reports results to ClickHouse.
    """

    users = []
    sent_event_count = 0
    ch_runs_table = "load_test_runs"

    def __init__(self, num_users: int, username_prefix: str, tags: List[str]):
        self.num_users = num_users
        self.username_prefix = username_prefix
        self.tags = tags
        self.run_id = str(uuid.uuid4())[:6]

        self.course_shortname = str(uuid.uuid4())[:6]

        self.ch_url = settings.EVENT_SINK_CLICKHOUSE_BACKEND_CONFIG["url"]
        self.ch_auth = ClickHouseAuth(
            settings.EVENT_SINK_CLICKHOUSE_BACKEND_CONFIG["username"],
            settings.EVENT_SINK_CLICKHOUSE_BACKEND_CONFIG["password"],
        )
        self.ch_database = settings.EVENT_SINK_CLICKHOUSE_BACKEND_CONFIG["database"]
        self.ch_xapi_database = settings.EVENT_SINK_CLICKHOUSE_BACKEND_CONFIG.get(
            "xapi_database", "xapi"
        )
        self.ch_runs_table = settings.EVENT_SINK_CLICKHOUSE_BACKEND_CONFIG.get(
            "runs_table", "load_test_runs"
        )
        self.ch_timeout_secs = settings.EVENT_SINK_CLICKHOUSE_BACKEND_CONFIG[
            "timeout_secs"
        ]

        self.instructor = self.create_user(
            username=f"instructor_{self.course_shortname}",
            name="Instructor",
            password="aspects",
            email=f"instructor_{self.course_shortname}@openedx.invalid",
        )
        self.create_course()
        self.record_start()
        self.create_and_enroll_learners(num_users, username_prefix)

    def create_course(self) -> None:
        """
        Create a course using the CMS API.
        """
        start_date = datetime.now() - timedelta(days=7)
        fields = {
            "start": start_date,
            "display_name": f"Course {self.course_shortname}",
        }

        log.info(
            f"""Creating course:
                Instructor: {self.instructor.id}
                Org: "OEX"
                Number: "{self.course_shortname}"
                Run: "2024-1"
                Fields: {fields}
                """
        )

        self.course = create_new_course_in_store(
            ModuleStoreEnum.Type.split,
            self.instructor,
            "OEX",
            self.course_shortname,
            "2024-1",
            fields,
        )

        log.info(f"Created course {self.course.id}")

    def record_start(self) -> None:
        """
        Send a start event to ClickHouse.

        Start and end events are used by the monitor script to know when to
        begin and end monitoring.
        """
        self.record_to_clickhouse(
            "start",
            {
                "tags": self.tags,
                "course_id": str(self.course.id),
                "num_users": self.num_users,
                "username_prefix": self.username_prefix,
            },
        )

        # Let the monitoring script connect, otherwise we can finish the test before it even
        # knows we've started.
        sleep(5)

    def record_end(self) -> None:
        """
        Send an end event to ClickHouse.
        """
        self.record_to_clickhouse("end", {"sent_event_count": self.sent_event_count})

    def record_to_clickhouse(self, event_type, extra) -> None:
        """
        Send the run events to ClickHouse.
        """
        insert = (
            f"INSERT INTO {self.ch_runs_table} (run_id, event_type, extra) FORMAT CSV "
        )

        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow((self.run_id, event_type, json.dumps(extra)))

        response = requests.post(
            url=self.ch_url,
            auth=self.ch_auth,
            params={"database": self.ch_database, "query": insert},
            data=output.getvalue().encode("utf-8"),
            timeout=self.ch_timeout_secs,
        )

        response.raise_for_status()

    def create_and_enroll_learners(self, num_users, username_prefix):
        """
        Uses create test users and enroll them in our test course.
        """
        log.info(f"Creating {num_users} users prefixed with {username_prefix}.")

        for _ in range(num_users):
            user_short_name = str(uuid.uuid4())[:6]
            u = self.create_user(
                username=f"{username_prefix}_{user_short_name}",
                name=f"Learner {user_short_name}",
                password="aspects",
                email=f"{user_short_name}@openedx.invalid",
            )
            self.users.append(u)
            e = CourseEnrollment.get_or_create_enrollment(
                user=u, course_key=self.course.id
            )
            e.is_active = True
            e.save()

    def create_user(self, **user_data):
        """
        Create, activate, and return a user using the edx-platform API.
        """
        account_creation_form = AccountCreationForm(data=user_data, tos_required=False)

        user, _, _ = do_create_account(account_creation_form)
        user.is_active = True
        user.save()
        return user

    def trigger_events(
        self, num_events: int, sleep_time: float, run_until_killed: bool
    ) -> None:
        """
        Trigger the appropriate number of events based on configuration.
        """

        if run_until_killed:
            log.info(f"Creating events until killed with {sleep_time} sleep between!")
            while True:
                self.trigger_event_and_sleep(sleep_time)
        else:
            log.info(f"Creating {num_events} event with {sleep_time} sleep between!")
            for _ in range(num_events):
                self.trigger_event_and_sleep(sleep_time)

    def trigger_event_and_sleep(self, sleep_time: float) -> None:
        """
        Cause a tracking log to be emitted and sleep the specified amount of time.
        """
        user = choice(self.users)

        e = CourseEnrollment.get_or_create_enrollment(
            user=user, course_key=self.course.id
        )

        if e.is_active:
            e.unenroll(user, self.course.id)
        else:
            e.enroll(user, self.course.id)  # pragma: no cover

        self.sent_event_count += 1
        sleep(sleep_time)


class Command(BaseCommand):
    """
    Create tracking log events for load testing purposes.

    Example:
    tutor local run lms ./manage.py lms load_test_tracking_events --sleep_time 0 --tags celery 1worker
    """

    help = dedent(__doc__).strip()

    def add_arguments(self, parser: Any) -> None:
        parser.add_argument(
            "--num_users",
            type=int,
            default=10,
            help="The number of users to create. All events will be generated for these learners.",
        )
        parser.add_argument(
            "--username_prefix",
            type=str,
            default="lt_",
            help="Prefix for the generated user names.",
        )
        parser.add_argument(
            "--num_events",
            type=int,
            default=10,
            help="The number of events to generate. This is ignored if --run_until_killed is set.",
        )
        parser.add_argument(
            "--run_until_killed",
            action="store_true",
            default=False,
            help="If this is set, the process will run endlessly until killed.",
        )
        parser.add_argument(
            "--sleep_time",
            type=float,
            default=0.75,
            help="Fractional number of seconds to sleep between sending events.",
        )
        parser.add_argument(
            "--tags",
            nargs="*",
            help="Tags to help define the run (ex: --tags celery 3workers k8s).",
        )

    def handle(self, *args, **options):
        """
        Create users and trigger events for them as configured above.
        """
        if not RUNNING_IN_PLATFORM:  # pragma: no cover
            raise CommandError("This command must be run in the Open edX LMS or CMS.")

        start = datetime.now()
        lt = LoadTest(options["num_users"], options["username_prefix"], options["tags"])

        try:
            lt.trigger_events(
                options["num_events"],
                options["sleep_time"],
                options["run_until_killed"],
            )
            lt.record_end()
        except KeyboardInterrupt:
            log.warning("Killed by keyboard, finishing.")
            lt.record_end()

        end = datetime.now()
        log.info(f"Sent {lt.sent_event_count} events in {end - start}.")

        # Wait 5 seconds for Kafka to clear the queue otherwise not all events
        # may be delivered.
        sleep(5)
