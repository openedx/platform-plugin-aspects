"""
Tests for the dump_data_to_clickhouse management command.
"""

from collections import namedtuple
from datetime import datetime

import django.core.management.base
import pytest
from django.core.management import call_command
from django_mock_queries.query import MockModel, MockSet

from platform_plugin_aspects.sinks.base_sink import ModelBaseSink

CommandOptions = namedtuple(
    "TestCommandOptions", ["options", "expected_num_submitted", "expected_logs"]
)


def dummy_model_factory():
    """
    Create a dummy model for testing.
    """

    class DummyModel:
        """
        Dummy model for testing.
        """

        def __init__(self, id):
            self.id = id
            self.created = datetime.now()

        @property
        def pk(self):
            return self.id

    return DummyModel


def dummy_serializer_factory():
    """
    Create a dummy serializer for testing.
    """

    class DummySerializer:
        """
        Dummy serializer for testing.
        """

        def __init__(self, model, many=False, initial=None):
            self.model = model
            self.many = many
            self.initial = initial

        @property
        def data(self):
            if self.many:
                return [{"id": item, "created": datetime.now()} for item in self.model]
            return {"id": self.model.id, "created": self.model.created}

    return DummySerializer


class DummySink(ModelBaseSink):
    """
    Dummy sink for testing.
    """

    name = "Dummy"
    model = "dummy"
    unique_key = "id"
    serializer_class = dummy_serializer_factory()
    timestamp_field = "created"
    clickhouse_table_name = "dummy_table"
    factory = dummy_model_factory()

    def get_queryset(self, start_pk=None):
        qs = MockSet(
            MockModel(mock_name="john", email="john@test.invalid", pk=1),
            MockModel(mock_name="jeff", email="jeff@test.invalid", pk=2),
            MockModel(mock_name="bill", email="bill@test.invalid", pk=3),
            MockModel(mock_name="joe", email="joe@test.invalid", pk=4),
            MockModel(mock_name="jim", email="jim@test.invalid", pk=5),
        )
        if start_pk:
            qs = qs.filter(pk__gt=start_pk)
        return qs

    def should_dump_item(self, unique_key):
        return unique_key.pk != 1, "No reason"

    def send_item_and_log(self, item_id, serialized_item, many):
        pass

    def get_object(self, item_id):
        return self.factory(item_id)


def dump_command_basic_options():
    """
    Pytest params for all the different non-ClickHouse command options.
    """
    options = [
        CommandOptions(
            options={"object": "dummy", "batch_size": 1, "sleep_time": 0},
            expected_num_submitted=4,
            expected_logs=[
                "Dumped 4 objects to ClickHouse",
            ],
        ),
        CommandOptions(
            options={"object": "dummy", "limit": 1, "batch_size": 1, "sleep_time": 0},
            expected_num_submitted=1,
            expected_logs=["Limit of 1 eligible objects has been reached, quitting!"],
        ),
        CommandOptions(
            options={"object": "dummy", "batch_size": 2, "sleep_time": 0},
            expected_num_submitted=2,
            expected_logs=[
                "Now dumping 2 Dummy to ClickHouse",
            ],
        ),
        CommandOptions(
            options={
                "object": "dummy",
                "batch_size": 1,
                "sleep_time": 0,
                "ids": ["1", "2", "3"],
            },
            expected_num_submitted=3,
            expected_logs=[
                "Now dumping 1 Dummy to ClickHouse",
                "Dumped 2 objects to ClickHouse",
                "Last ID: 3"
            ],
        ),
        CommandOptions(
            options={
                "object": "dummy",
                "batch_size": 1,
                "sleep_time": 0,
                "start_pk": 1,
            },
            expected_num_submitted=4,
            expected_logs=[
                "Now dumping 1 Dummy to ClickHouse",
                "Dumped 4 objects to ClickHouse",
            ],
        ),
        CommandOptions(
            options={
                "object": "dummy",
                "batch_size": 1,
                "sleep_time": 0,
                "force": True,
            },
            expected_num_submitted=4,
            expected_logs=[
                "Now dumping 1 Dummy to ClickHouse",
                "Dumped 5 objects to ClickHouse",
            ],
        ),
        CommandOptions(
            options={
                "object": "dummy",
                "batch_size": 2,
                "sleep_time": 0,
                "ids_to_skip": ["3", "4", "5"],
            },
            expected_num_submitted=4,
            expected_logs=[
                "Now dumping 1 Dummy to ClickHouse",
                "Dumped 1 objects to ClickHouse",
            ],
        ),
    ]

    for option in options:
        yield option


@pytest.mark.parametrize("test_command_option", dump_command_basic_options())
def test_dump_courses_options(test_command_option, caplog):
    option_combination, expected_num_submitted, expected_outputs = test_command_option

    assert DummySink.model in [cls.model for cls in ModelBaseSink.__subclasses__()]

    call_command("dump_data_to_clickhouse", **option_combination)

    for expected_output in expected_outputs:
        assert expected_output in caplog.text


def dump_basic_invalid_options():
    """
    Pytest params for all the different non-ClickHouse command options.
    """
    options = [
        CommandOptions(
            options={"object": "dummy", "limit": 1, "force": True},
            expected_num_submitted=1,
            expected_logs=[],
        ),
        CommandOptions(
            options={"object": "dummy", "limit": 1, "force": True},
            expected_num_submitted=1,
            expected_logs=[],
        ),
        CommandOptions(
            options={"object": "dummy", "limit": 0, "force": True},
            expected_num_submitted=1,
            expected_logs=[],
        ),
        CommandOptions(
            options={},
            expected_num_submitted=1,
            expected_logs=[],
        ),
    ]

    for option in options:
        yield option


@pytest.mark.parametrize("test_command_option", dump_basic_invalid_options())
def test_dump_courses_options_invalid(test_command_option, caplog):
    option_combination, expected_num_submitted, expected_outputs = test_command_option
    assert DummySink.model in [cls.model for cls in ModelBaseSink.__subclasses__()]

    with pytest.raises(django.core.management.base.CommandError):
        call_command("dump_data_to_clickhouse", **option_combination)
    # assert mock_dump_data.apply_async.call_count == expected_num_submitted
    for expected_output in expected_outputs:
        assert expected_output in caplog.text
