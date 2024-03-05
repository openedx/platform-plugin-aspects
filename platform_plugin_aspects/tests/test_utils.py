"""
Test utils.
"""

from collections import namedtuple
from unittest import TestCase
from unittest.mock import Mock, patch

from django.conf import settings

from platform_plugin_aspects.utils import (
    generate_superset_context,
    get_ccx_courses,
    get_model,
)

User = namedtuple("User", ["username"])


class TestUtils(TestCase):
    """
    Test utils module
    """

    @patch("platform_plugin_aspects.utils.import_module")
    @patch.object(
        settings,
        "EVENT_SINK_CLICKHOUSE_MODEL_CONFIG",
        {"my_model": {"module": "myapp.models", "model": "MyModel"}},
    )
    @patch("platform_plugin_aspects.utils.logger")
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

        get_ccx_courses("dummy_key")

        mock_model.objects.filter.assert_called_once_with(course_id="dummy_key")

    @patch.object(settings, "FEATURES", {"CUSTOM_COURSES_EDX": False})
    def test_get_ccx_courses_feature_disabled(self):
        courses = get_ccx_courses("dummy_key")

        self.assertEqual(list(courses), [])

    @patch("platform_plugin_aspects.utils.generate_guest_token")
    def test_generate_superset_context(self, mock_generate_guest_token):
        """
        Test generate_superset_context
        """
        course_mock = Mock()
        filter_mock = Mock()
        context = {"course": course_mock}
        mock_generate_guest_token.return_value = ("test-token", "test-dashboard-uuid")

        context = generate_superset_context(
            context,
            dashboard_uuid="test-dashboard-uuid",
            filters=[filter_mock],
        )

        self.assertEqual(context["superset_token"], "test-token")
        self.assertEqual(context["dashboard_uuid"], "test-dashboard-uuid")
        self.assertEqual(context["superset_url"], settings.SUPERSET_CONFIG.get("host"))
        self.assertNotIn("exception", context)

    @patch("platform_plugin_aspects.utils.SupersetClient")
    def test_generate_superset_context_with_superset_client_exception(
        self, mock_superset_client
    ):
        """
        Test generate_superset_context
        """
        course_mock = Mock()
        filter_mock = Mock()
        context = {"course": course_mock}
        mock_superset_client.side_effect = Exception("test-exception")

        context = generate_superset_context(
            context,
            dashboard_uuid="test-dashboard-uuid",
            filters=[filter_mock],
        )

        self.assertIn("exception", context)

    @patch("platform_plugin_aspects.utils.SupersetClient")
    @patch("platform_plugin_aspects.utils.get_current_user")
    def test_generate_superset_context_succesful(
        self, mock_get_current_user, mock_superset_client
    ):
        """
        Test generate_superset_context
        """
        course_mock = Mock()
        filter_mock = Mock()
        context = {"course": course_mock}
        response_mock = Mock(status_code=200)
        mock_superset_client.return_value.session.post.return_value = response_mock
        response_mock.json.return_value = {
            "token": "test-token",
        }
        mock_get_current_user.return_value = User(username="test-user")

        context = generate_superset_context(
            context,
            dashboard_uuid="test-dashboard-uuid",
            filters=[filter_mock],
        )

        self.assertEqual(context["superset_token"], "test-token")
        self.assertEqual(context["dashboard_uuid"], "test-dashboard-uuid")
        self.assertEqual(context["superset_url"], settings.SUPERSET_CONFIG.get("host"))

    @patch("platform_plugin_aspects.utils.get_current_user")
    def test_generate_superset_context_with_exception(self, mock_get_current_user):
        """
        Test generate_superset_context
        """
        course_mock = Mock()
        filter_mock = Mock()
        mock_get_current_user.return_value = User(username="test-user")
        context = {"course": course_mock}

        context = generate_superset_context(
            context,
            dashboard_uuid="test-dashboard-uuid",
            filters=[filter_mock],
        )

        self.assertIn("exception", context)
