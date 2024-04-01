"""
Tests for the monitor_load_test_tracking management command.
"""

import datetime
from collections import namedtuple
from unittest.mock import DEFAULT, Mock, patch

import pytest
from django.core.management import call_command

CommandOptions = namedtuple("TestCommandOptions", ["options", "expected_logs"])
KafkaPartition = namedtuple("KafkaPartition", ["offset", "topic", "partition"])


def load_test_command_basic_options():
    """
    Pytest params for all the different non-ClickHouse command options.
    """
    options = [
        # Test our defaults
        CommandOptions(
            options={},
            expected_logs=[
                "Clickhouse lag seconds: 1",
                "Celery queues: LMS 0, CMS 0",
                "Starting monitor for celery with sleep of 10 seconds",
            ],
        ),
        # Test overriding sleep time
        CommandOptions(
            options={"sleep_time": 5},
            expected_logs=[
                "Clickhouse lag seconds: 1",
                "Celery queues: LMS 0, CMS 0",
                "Starting monitor for celery with sleep of 5 seconds",
            ],
        ),
        # Test explicit celery backend
        CommandOptions(
            options={"backend": "celery"},
            expected_logs=[
                "Clickhouse lag seconds: 1",
                "Celery queues: LMS 0, CMS 0",
                "Starting monitor for celery with sleep of 10 seconds",
            ],
        ),
        # Test redis bus backend
        CommandOptions(
            options={"backend": "redis_bus"},
            expected_logs=[
                "Clickhouse lag seconds: 1",
                "Starting monitor for redis_bus with sleep of 10 seconds",
                "Redis bus queue length: 0",
            ],
        ),
        # Test kafka bus backend
        CommandOptions(
            options={"backend": "kafka_bus"},
            expected_logs=[
                "Clickhouse lag seconds: 1",
                "Starting monitor for kafka_bus with sleep of 10 seconds",
                "test [test] Lag: 0",
            ],
        ),
        # Test vector backend
        CommandOptions(
            options={"backend": "vector"},
            expected_logs=[
                "Clickhouse lag seconds: 1",
                "Vector received: 10 sent: 10 lag: 0",
                "Starting monitor for vector with sleep of 10 seconds",
            ],
        ),
    ]

    for option in options:
        yield option


@pytest.mark.parametrize("test_command_option", load_test_command_basic_options())
def test_monitor_options(test_command_option, caplog):
    option_combination, expected_outputs = test_command_option
    patch_prefix = (
        "platform_plugin_aspects.management.commands.monitor_load_test_tracking"
    )

    with patch.multiple(
        f"{patch_prefix}",
        requests=DEFAULT,
        settings=DEFAULT,
        redis=DEFAULT,
        json=DEFAULT,
        confluent_kafka=DEFAULT,
        sleep=DEFAULT,
    ) as patches:
        # First response is the ClickHouse call to get the run id
        patches["requests"].post.return_value.text.strip.return_value = "runabc"

        # Then the call to get clickhouse lag data
        patches["requests"].post.return_value.json.side_effect = (
            {
                "data": [
                    {
                        "lag_seconds": 1,
                        "ttl_count": 100,
                        "most_recent": datetime.datetime.now().isoformat(),
                    },
                ]
            },
            # Then the Vector API call, GraphQL is awful.
            {
                "data": {
                    "sinks": {
                        "edges": [
                            {
                                "node": {
                                    "metrics": {
                                        "sentEventsTotal": {"sentEventsTotal": 10},
                                        "receivedEventsTotal": {
                                            "receivedEventsTotal": 10
                                        },
                                    },
                                },
                            }
                        ],
                    }
                }
            },
        )

        patches["redis"].Redis.from_url.return_value.llen.return_value = 0
        patches["redis"].Redis.from_url.return_value.xinfo_stream.return_value = {
            "length": 100,
            "groups": [
                {"name": "group1", "lag": 0},
                {"name": "group2", "lag": 0},
            ],
        }

        patches["confluent_kafka"].Consumer.return_value.committed.return_value = {
            KafkaPartition(offset=10, topic="test", partition="test"): Mock()
        }

        patches[
            "confluent_kafka"
        ].Consumer.return_value.get_watermark_offsets.return_value = (10, 10)

        call_command("monitor_load_test_tracking", **option_combination)

    print(caplog.text)

    for expected_output in expected_outputs:
        assert expected_output in caplog.text
