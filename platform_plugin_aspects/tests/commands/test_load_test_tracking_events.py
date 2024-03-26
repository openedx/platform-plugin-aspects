"""
Tests for the load_test_tracking_events management command.
"""

from collections import namedtuple
from unittest.mock import DEFAULT, Mock, patch

import pytest
from django.core.management import call_command

CommandOptions = namedtuple("TestCommandOptions", ["options", "expected_logs"])


def load_test_command_basic_options():
    """
    Pytest params for all the different non-ClickHouse command options.

            "--num_users",
            "--username_prefix",
            "--num_events",
            "--run_until_killed",
            "--sleep_time",
    """
    options = [
        CommandOptions(
            options={"sleep_time": 0},
            expected_logs=[
                "events in",
                "Creating 10 users prefixed with lt_",
                "Creating 10 event with 0 sleep between!",
            ],
        ),
        CommandOptions(
            options={"sleep_time": 0.1, "num_users": 2, "username_prefix": "cheese_"},
            expected_logs=[
                "events in",
                "Creating 2 users prefixed with cheese_",
                "Creating 10 event with 0.1 sleep between!",
            ],
        ),
    ]

    for option in options:
        yield option


@pytest.mark.parametrize("test_command_option", load_test_command_basic_options())
def test_load_test_options(test_command_option, caplog):
    option_combination, expected_outputs = test_command_option

    fake_course = Mock()
    fake_course.return_value.id = "fake_course_id"

    patch_prefix = (
        "platform_plugin_aspects.management.commands.load_test_tracking_events"
    )
    with patch.multiple(
        f"{patch_prefix}",
        create_new_course_in_store=fake_course,
        do_create_account=lambda _: (Mock(), DEFAULT, DEFAULT),
        CourseEnrollment=DEFAULT,
        AccountCreationForm=DEFAULT,
        ModuleStoreEnum=DEFAULT,
        RUNNING_IN_PLATFORM=True,
        requests=DEFAULT,
        sleep=DEFAULT,
    ) as _:
        call_command("load_test_tracking_events", **option_combination)

    print(caplog.text)

    for expected_output in expected_outputs:
        assert expected_output in caplog.text


def test_load_test_run_until_killed(caplog):
    fake_course = Mock()
    fake_course.return_value.id = "fake_course_id"

    patch_prefix = (
        "platform_plugin_aspects.management.commands.load_test_tracking_events"
    )

    def fake_sleep_or_raise(sleep_time):
        # Magic 5 is the hard coded time for start/end events
        if sleep_time == 5:
            return
        # We use the sleep at the end of the loop to break out of it
        else:
            raise KeyboardInterrupt()

    with patch.multiple(
        f"{patch_prefix}",
        create_new_course_in_store=fake_course,
        do_create_account=lambda _: (Mock(), DEFAULT, DEFAULT),
        CourseEnrollment=DEFAULT,
        AccountCreationForm=DEFAULT,
        ModuleStoreEnum=DEFAULT,
        RUNNING_IN_PLATFORM=True,
        requests=DEFAULT,
        sleep=Mock(side_effect=fake_sleep_or_raise),
    ) as _:
        call_command(
            "load_test_tracking_events", **{"run_until_killed": True, "sleep_time": 0}
        )

    print(caplog.text)

    assert f"Creating events until killed with 0 sleep between!" in caplog.text
    assert f"Killed by keyboard, finishing" in caplog.text
