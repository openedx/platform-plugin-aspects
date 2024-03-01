"""
Tests for the tasks module.
"""
import unittest
from unittest.mock import MagicMock, patch

from platform_plugin_aspects.tasks import dump_data_to_clickhouse


class TestTasks(unittest.TestCase):
    """
    Test cases for tasks.
    """

    @patch("platform_plugin_aspects.tasks.import_module")
    @patch("platform_plugin_aspects.tasks.celery_log")
    def test_dump_data_to_clickhouse(self, mock_celery_log, mock_import_module):
        # Mock the required objects and methods
        mock_Sink_class = MagicMock()
        mock_Sink_instance = mock_Sink_class.return_value
        mock_Sink_instance.dump.return_value = None
        mock_import_module.return_value = MagicMock(**{"sink_name": mock_Sink_class})

        # Call the function
        dump_data_to_clickhouse(
            "sink_module",
            "sink_name",
            "object_id",
            connection_overrides={"param": "value"},
        )

        # Assertions
        mock_import_module.assert_called_once_with("sink_module")
        mock_Sink_class.assert_called_once_with(
            connection_overrides={"param": "value"}, log=mock_celery_log
        )
        mock_Sink_instance.dump.assert_called_once_with("object_id")

    @patch("platform_plugin_aspects.tasks.import_module")
    def test_dump_data_to_clickhouse_disabled_sink(
        self, mock_import_module
    ):
        # Mock the required objects and methods
        mock_Sink_class = MagicMock()
        mock_Sink_class.is_enabled.return_value = False
        mock_Sink_instance = mock_Sink_class.return_value
        mock_Sink_instance.dump.return_value = None
        mock_import_module.return_value = MagicMock(**{"sink_name": mock_Sink_class})

        dump_data_to_clickhouse(
            "sink_module",
            "sink_name",
            "object_id",
            connection_overrides={"param": "value"},
        )

        # Assertions
        mock_import_module.assert_called_once_with("sink_module")
        mock_Sink_class.assert_not_called()
        mock_Sink_instance.dump.assert_not_called()
