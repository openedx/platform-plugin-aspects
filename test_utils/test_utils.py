"""
Test utils.
"""
import unittest
from unittest.mock import Mock, patch

from django.conf import settings

from platform_plugin_aspects.utils import get_ccx_courses, get_model


class TestUtils(unittest.TestCase):
    """
    Test utils
    """

    @patch("platform_plugin_aspects.utils.import_module")
    @patch.object(
        settings,
        "EVENT_SINK_CLICKHOUSE_MODEL_CONFIG",
        {"my_model": {"module": "myapp.models", "model": "MyModel"}},
    )
    @patch("platform_plugin_aspects.utils.log")
    def test_get_model_success(self, mock_log, mock_import_module):
        mock_model = Mock(__name__="MyModel")
        mock_import_module.return_value = Mock(MyModel=mock_model)

        model = get_model("my_model")

        mock_import_module.assert_called_once_with("myapp.models")
        self.assertIsNotNone(model)
        self.assertEqual(model.__name__, "MyModel")
        mock_log.assert_not_called()

    @patch.object(
        settings,
        "EVENT_SINK_CLICKHOUSE_MODEL_CONFIG",
        {"my_model": {"module": "myapp.models", "model": "NonExistentModel"}},
    )
    def test_get_model_non_existent_model(self):
        model = get_model("my_model")
        self.assertIsNone(model)

    @patch.object(
        settings,
        "EVENT_SINK_CLICKHOUSE_MODEL_CONFIG",
        {"my_model": {"module": "non_existent_module", "model": "MyModel"}},
    )
    def test_get_model_non_existent_module(self):
        model = get_model("my_model")

        self.assertIsNone(model)

    @patch.object(
        settings, "EVENT_SINK_CLICKHOUSE_MODEL_CONFIG", {"my_model": {"module": ""}}
    )
    def test_get_model_missing_module_and_model(self):
        model = get_model("my_model")
        self.assertIsNone(model)

    @patch.object(settings, "EVENT_SINK_CLICKHOUSE_MODEL_CONFIG", {})
    def test_get_model_missing_module_and_model_2(self):
        model = get_model("my_model")
        self.assertIsNone(model)

    @patch.object(
        settings,
        "EVENT_SINK_CLICKHOUSE_MODEL_CONFIG",
        {"my_model": {"module": "myapp.models"}},
    )
    def test_get_model_missing_model_config(self):
        model = get_model("my_model")
        self.assertIsNone(model)

    @patch("platform_plugin_aspects.utils.get_model")
    def test_get_ccx_courses(self, mock_get_model):
        mock_get_model.return_value = mock_model = Mock()

        get_ccx_courses('dummy_key')

        mock_model.objects.filter.assert_called_once_with(course_id='dummy_key')

    @patch.object(settings, "FEATURES", {"CUSTOM_COURSES_EDX": False})
    def test_get_ccx_courses_feature_disabled(self):
        courses = get_ccx_courses('dummy_key')

        self.assertEqual(list(courses), [])
