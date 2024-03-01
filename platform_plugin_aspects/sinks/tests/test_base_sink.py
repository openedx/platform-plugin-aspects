"""
Tests for the base sinks.
"""

import logging
from unittest.mock import MagicMock, Mock, patch

import ddt
from django.test import TestCase
from django.test.utils import override_settings

from platform_plugin_aspects.sinks.base_sink import ModelBaseSink


class ChildSink(ModelBaseSink):  # pylint: disable=abstract-method
    """
    Demo child sink.
    """

    nested_sinks = [MagicMock()]
    model = "child_model"
    unique_key = "id"
    clickhouse_table_name = "child_model_table"
    timestamp_field = "time_last_dumped"
    name = "Child Model"
    serializer_class = Mock()


@override_settings(
    EVENT_SINK_CLICKHOUSE_BACKEND_CONFIG={
        "url": "http://clickhouse:8123",
        "username": "ch_cms",
        "password": "password",
        "database": "event_sink",
        "timeout_secs": 5,
    },
    EVENT_SINK_CLICKHOUSE_MODEL_CONFIG={},
)
class TestBaseSink(TestCase):
    """
    Tests for the BaseSink.
    """

    def test_connection_overrides(self):
        """
        Test that connection_overrides() returns the correct data.
        """
        child_sink = ChildSink(
            connection_overrides={
                "url": "http://dummy:8123",
                "username": "dummy_username",
                "password": "dummy_password",
                "database": "dummy_database",
                "timeout_secs": 0,
            },
            log=logging.getLogger(),
        )

        self.assertEqual(child_sink.ch_url, "http://dummy:8123")
        self.assertEqual(child_sink.ch_auth, ("dummy_username", "dummy_password"))
        self.assertEqual(child_sink.ch_database, "dummy_database")
        self.assertEqual(child_sink.ch_timeout_secs, 0)


@override_settings(
    EVENT_SINK_CLICKHOUSE_BACKEND_CONFIG={
        # URL to a running ClickHouse server's HTTP interface. ex: https://foo.openedx.org:8443/ or
        # http://foo.openedx.org:8123/ . Note that we only support the ClickHouse HTTP interface
        # to avoid pulling in more dependencies to the platform than necessary.
        "url": "http://clickhouse:8123",
        "username": "ch_cms",
        "password": "password",
        "database": "event_sink",
        "timeout_secs": 5,
    },
    EVENT_SINK_CLICKHOUSE_MODEL_CONFIG={},
)
@ddt.ddt
class TestModelBaseSink(TestCase):
    """
    Tests for the ModelBaseSink.
    """

    def setUp(self):
        """
        Set up the test suite.
        """
        self.child_sink = ChildSink(connection_overrides={}, log=logging.getLogger())

    @ddt.data(
        (1, {"dump_id": 1, "time_last_dumped": "2020-01-01 00:00:00"}, False),
        (
            [1, 2],
            [
                {"dump_id": 1, "time_last_dumped": "2020-01-01 00:00:00"},
                {"dump_id": 2, "time_last_dumped": "2020-01-01 00:00:00"},
            ],
            True,
        ),
    )
    @ddt.unpack
    def test_dump(self, items_id, serialized_items, many):
        """
        Test that the serialization/send logic is called correctly with many=True and many=False.
        """
        self.child_sink.send_item_and_log = Mock()
        self.child_sink.serialize_item = Mock(return_value=serialized_items)
        self.child_sink.get_object = Mock(return_value=items_id)

        self.child_sink.dump(items_id, many=many)

        self.child_sink.serialize_item.assert_called_once_with(
            items_id, many=many, initial=None
        )
        self.child_sink.send_item_and_log.assert_called_once_with(
            items_id, self.child_sink.serialize_item.return_value, many
        )

    def test_send_item_and_log(self):
        """
        Test that send_item is called correctly.
        """
        item = Mock(id=1)
        self.child_sink.send_item = Mock()
        serialized_item = {"dump_id": 1, "time_last_dumped": "2020-01-01 00:00:00"}

        self.child_sink.send_item_and_log(item.id, serialized_item, many=False)

        self.child_sink.send_item.assert_called_once_with(serialized_item, many=False)

    def test_serialize_item(self):
        """
        Test that serialize_item() returns the correct serialized data.
        """
        item = Mock(id=1)
        serialized_item = {"dump_id": 1, "time_last_dumped": "2020-01-01 00:00:00"}
        self.child_sink.get_serializer = Mock(data=serialized_item)
        self.child_sink.send_item_and_log = Mock()

        serialized_item = self.child_sink.serialize_item(item, many=False, initial=None)

        self.child_sink.get_serializer.return_value.assert_called_once_with(
            item,
            many=False,
            initial=None,
        )
        self.assertEqual(
            serialized_item,
            self.child_sink.get_serializer.return_value.return_value.data,
        )

    @patch("platform_plugin_aspects.sinks.base_sink.io")
    @patch("platform_plugin_aspects.sinks.base_sink.requests")
    @ddt.data(
        ({"dump_id": 1, "time_last_dumped": "2020-01-01 00:00:00"}, False),
        (
            [
                {"dump_id": 1, "time_last_dumped": "2020-01-01 00:00:00"},
                {"dump_id": 2, "time_last_dumped": "2020-01-01 00:00:00"},
            ],
            True,
        ),
    )
    @ddt.unpack
    def test_send_items(self, serialized_items, many, mock_requests, mock_io):
        """
        Test that send_item() calls the correct requests.
        """
        params = self.child_sink.CLICKHOUSE_BULK_INSERT_PARAMS.copy()
        params["query"] = "INSERT INTO event_sink.child_model_table FORMAT CSV"
        self.child_sink._send_clickhouse_request = (  # pylint: disable=protected-access
            Mock()
        )
        data = "1,2020-01-01 00:00:00\n2,2020-01-01 00:00:00\n"
        mock_io.StringIO.return_value.getvalue.return_value.encode.return_value = data

        self.child_sink.send_item(serialized_items, many=many)

        mock_requests.Request.assert_called_once_with(
            "POST",
            self.child_sink.ch_url,
            data=data,
            params=params,
            auth=self.child_sink.ch_auth,
        )
        self.child_sink._send_clickhouse_request(  # pylint: disable=protected-access
            mock_requests.Request.return_value
        )

    def test_init(self):
        # Mock the required fields
        connection_overrides = {}
        log = MagicMock()

        # Test without all required fields
        with self.assertRaises(NotImplementedError):
            sink = ModelBaseSink(connection_overrides, log)
            self.assertIsInstance(sink, ModelBaseSink)

    def fetch_target_items(self):
        """
        Test that fetch_target_items() returns the correct data.
        """

    def test_get_last_dumped_timestamp(self):
        """
        Test that get_last_dumped_timestamp() returns the correct data.
        """

    @override_settings(
        EVENT_SINK_CLICKHOUSE_MODEL_CONFIG={
            "child_model": {
                "module": "dummy.module",
                "model": "dummy",
            },
        }
    )
    @patch("platform_plugin_aspects.sinks.base_sink.get_model")
    def test_get_model(self, mock_get_model):
        """
        Test that get_model() returns a query set.
        """
        self.child_sink.get_model()
        mock_get_model.assert_called_once_with("child_model")

    def test_get_queryset(self):
        """
        Test that get_queryset() returns a query set.
        """
        self.child_sink.get_model = Mock()
        self.child_sink.get_queryset()
        self.child_sink.get_model.return_value.objects.all.assert_called_once()

    def test_get_queryset_by_start_pk(self):
        """
        Test that get_queryset() returns a query set.
        """
        self.child_sink.get_model = Mock()
        self.child_sink.get_queryset(start_pk=1)
        self.child_sink.get_model.return_value.objects.filter.assert_called_once_with(
            pk__gt=1
        )

    def test_nested_sink_dump_related(self):
        """
        Test that dump_related() calls the correct methods.
        """
        self.child_sink.dump = Mock()
        with self.assertRaises(NotImplementedError):
            self.child_sink.dump_related("foo", "bar", "baz")

    def test_get_serializer(self):
        """
        Test that get_serializer() returns the correct serializer.
        """
        serializer = self.child_sink.get_serializer()
        self.assertEqual(serializer, self.child_sink.serializer_class)

    def test_should_dump_item(self):
        """
        Test that should_dump_item() returns the correct data.
        """
        self.assertEqual(self.child_sink.should_dump_item(1), (True, "No reason"))

    @patch("platform_plugin_aspects.sinks.base_sink.WaffleFlag.is_enabled")
    def test_is_not_enabled_waffle(self, mock_waffle_flag_is_enabled):
        """
        Test that is_enable() returns the correct data.
        """
        mock_waffle_flag_is_enabled.return_value = False
        self.assertEqual(self.child_sink.__class__.is_enabled(), False)

    @patch("platform_plugin_aspects.sinks.base_sink.WaffleFlag.is_enabled")
    def test_is_enabled_waffle(self, mock_waffle_flag_is_enabled):
        """
        Test that is_enable() returns the correct data.
        """
        mock_waffle_flag_is_enabled.return_value = True
        self.assertEqual(self.child_sink.__class__.is_enabled(), True)

    @override_settings(EVENT_SINK_CLICKHOUSE_CHILD_MODEL_ENABLED=True)
    def test_is_enabled(self):
        """
        Test that is_enable() returns the correct data.
        """
        self.assertEqual(self.child_sink.is_enabled(), True)

    def test_get_sink_by_model_name(self):
        """
        Test that get_sink_by_model_name() returns the correct data.
        """
        no_sink = ModelBaseSink.get_sink_by_model_name("non_existent_model")
        child_sink = ModelBaseSink.get_sink_by_model_name("child_model")

        self.assertIsNone(no_sink)
        self.assertEqual(child_sink, ChildSink)
