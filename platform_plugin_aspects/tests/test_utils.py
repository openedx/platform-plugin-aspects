"""
Test utils.
"""

from unittest.mock import Mock, patch

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.test import TestCase

from platform_plugin_aspects.utils import (
    generate_guest_token,
    generate_superset_context,
    get_ccx_courses,
    get_model,
)

COURSE_ID = "course-v1:org+course+run"


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

    @patch.object(
        settings,
        "SUPERSET_CONFIG",
        {
            "internal_service_url": "http://superset:8088",
            "service_url": "http://superset-dummy-url/",
            "username": "superset",
            "password": "superset",
        },
    )
    def test_generate_superset_context(self):
        """
        Test generate_superset_context
        """
        context = {"course": COURSE_ID}
        dashboards = settings.ASPECTS_INSTRUCTOR_DASHBOARDS

        dashboards.append(
            {
                "slug": "test-slug",
                "uuid": "3ea6e738-989d-4325-8f93-82bb684dab5c",
                "allow_translations": False,
            }
        )

        context = generate_superset_context(
            context,
            dashboards=dashboards,
            language="en_US",
        )

        self.assertEqual(
            context["superset_guest_token_url"], f"/superset_guest_token/{COURSE_ID}"
        )
        self.assertEqual(context["superset_dashboards"], dashboards)
        self.assertEqual(context["superset_url"], "http://superset-dummy-url/")
        self.assertNotIn("superset_token", context)
        self.assertNotIn("exception", context)

    @patch("platform_plugin_aspects.utils.SupersetClient")
    def test_generate_guest_token_with_superset_client_exception(
        self, mock_superset_client
    ):
        """
        Test generate_guest_token
        """
        filter_mock = Mock()
        user_mock = Mock()
        mock_superset_client.side_effect = Exception("test-exception")

        with self.assertRaises(ImproperlyConfigured):
            generate_guest_token(
                user=user_mock,
                course=COURSE_ID,
                dashboards=[{"name": "test", "uuid": "test-dashboard-uuid"}],
                filters=[filter_mock],
            )

        mock_superset_client.assert_called_once()

    @patch.object(
        settings,
        "SUPERSET_CONFIG",
        {
            "internal_service_url": "http://superset:8088",
            "service_url": "http://dummy-superset-url",
            "username": "superset",
            "password": "superset",
        },
    )
    @patch("platform_plugin_aspects.utils.SupersetClient")
    def test_generate_guest_token_succesful(self, mock_superset_client):
        """
        Test generate_guest_token
        """
        response_mock = Mock(status_code=200)
        mock_superset_client.return_value.session.post.return_value = response_mock
        response_mock.json.return_value = {
            "token": "test-token",
        }

        filter_mock = Mock()
        user_mock = Mock()
        dashboards = [{"name": "test", "uuid": "test-dashboard-uuid"}]

        token = generate_guest_token(
            user=user_mock,
            course=COURSE_ID,
            dashboards=dashboards,
            filters=[filter_mock],
        )

        mock_superset_client.assert_called_once()
        self.assertEqual(token, "test-token")
