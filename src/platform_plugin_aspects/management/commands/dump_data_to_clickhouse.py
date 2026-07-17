"""
Management command for exporting the modulestore ClickHouse.

Example usages (see usage for more options):

    # Dump all objects published since last dump.
    # Use connection parameters from `settings.EVENT_SINK_CLICKHOUSE_BACKEND_CONFIG`:
    python manage.py cms dump_objects_to_clickhouse --object user_profile

    # Specify certain objects instead of dumping all of them.
    # Use connection parameters from `settings.EVENT_SINK_CLICKHOUSE_BACKEND_CONFIG`.
    python manage.py cms dump_objects_to_clickhouse --object user_profile --objects 123 124 125

    # Dump a limited number of objects to prevent stress on production systems
    python manage.py cms dump_objects_to_clickhouse --limit 1000
"""

import logging
import time
from textwrap import dedent

from django.core.management.base import BaseCommand, CommandError

from platform_plugin_aspects.sinks.base_sink import ModelBaseSink

log = logging.getLogger(__name__)


def dump_target_objects_to_clickhouse(
    sink=None,
    start_pk=None,
    object_ids=None,
    objects_to_skip=None,
    force=False,
    limit=None,
    batch_size=1000,
    sleep_time=10,
):
    """
    Iterates through a list of objects in the ORN, serializes them to csv,
    then submits tasks to post them to ClickHouse.

    Arguments:
        force: serialize the objects even if they've been recently
            serialized

    Returns: two lists--one of the objects that had dump jobs queued for them
        and one of objects that did not.
    """

    count = 0
    skipped_objects = []
    objects_to_submit = []

    for obj, should_be_dumped, reason in sink.fetch_target_items(
        start_pk, object_ids, objects_to_skip, force, batch_size
    ):
        if not should_be_dumped:
            skipped_objects.append(obj.pk)
            log.info(f"{sink.model}: Skipping object {obj.pk}, reason: '{reason}'")
        else:
            objects_to_submit.append(obj)
            if len(objects_to_submit) % batch_size == 0:
                count += len(objects_to_submit)
                sink.dump(objects_to_submit, many=True)
                objects_to_submit = []
                log.info(f"Last ID: {obj.pk}")
                time.sleep(sleep_time)

            if limit and count == limit:
                log.info(
                    f"Limit of {limit} eligible objects has been reached, quitting!"
                )
                break

    if objects_to_submit:
        sink.dump(objects_to_submit, many=True)
        count += len(objects_to_submit)
        log.info(f"Last ID: {objects_to_submit[-1].pk}")

    log.info(f"Dumped {count} objects to ClickHouse")


class Command(BaseCommand):
    """
    Dump objects to a ClickHouse instance.
    """

    help = dedent(__doc__).strip()

    def add_arguments(self, parser):
        parser.add_argument(
            "--url",
            type=str,
            help="the URL of the ClickHouse server",
        )
        parser.add_argument(
            "--username",
            type=str,
            help="the username of the ClickHouse user",
        )
        parser.add_argument(
            "--password",
            type=str,
            help="the password of the ClickHouse user",
        )
        parser.add_argument(
            "--database",
            type=str,
            help="the database in ClickHouse to connect to",
        )
        parser.add_argument(
            "--timeout_secs",
            type=int,
            help="timeout for ClickHouse requests, in seconds",
        )
        parser.add_argument(
            "--object",
            type=str,
            help="the type of object to dump",
        )
        parser.add_argument(
            "--start_pk",
            type=int,
            help="the primary key to start at",
            default=None,
        )
        parser.add_argument(
            "--ids",
            metavar="KEY",
            type=str,
            nargs="*",
            help="keys of objects to serialize; if omitted all objects in system are serialized",
        )
        parser.add_argument(
            "--ids_to_skip",
            metavar="KEY",
            type=str,
            nargs="*",
            help="keys of objects to NOT to serialize",
        )
        parser.add_argument(
            "--force",
            action="store_true",
            help="dump all objects regardless of when they were last published",
        )
        parser.add_argument(
            "--limit",
            type=int,
            help="maximum number of objects to dump, cannot be used with '--ids' or '--force'",
        )
        parser.add_argument(
            "--batch_size",
            type=int,
            default=10000,
            help="number of objects to dump in a single batch",
        )
        parser.add_argument(
            "--sleep_time",
            type=int,
            default=1,
            help="number of seconds to sleep between batches",
        )

    def handle(self, *args, **options):
        """
        Iterates through each objects, serializes and saves them to clickhouse.
        """
        connection_overrides = {
            key: options[key]
            for key in ["url", "username", "password", "database", "timeout_secs"]
            if options[key]
        }

        ids = options["ids"] if options["ids"] else []
        ids_to_skip = options["ids_to_skip"] if options["ids_to_skip"] else []

        if options["limit"] is not None and int(options["limit"]) < 1:
            message = "'limit' must be greater than 0!"
            log.error(message)
            raise CommandError(message)

        if options["limit"] and options["force"]:
            message = (
                "The 'limit' option cannot be used with 'force' as running the "
                "command repeatedly will result in the same objects being dumped every time."
            )
            log.error(message)
            raise CommandError(message)

        if options["object"] is None:
            message = "You must specify an object type to dump!"
            log.error(message)
            raise CommandError(message)

        Sink = ModelBaseSink.get_sink_by_model_name(options["object"])
        sink = Sink(connection_overrides, log)
        dump_target_objects_to_clickhouse(
            sink,
            options["start_pk"],
            [object_id.strip() for object_id in ids],
            [object_id.strip() for object_id in ids_to_skip],
            options["force"],
            options["limit"],
            options["batch_size"],
            options["sleep_time"],
        )
