"""
Test utils.
"""

from collections import namedtuple
from unittest.mock import Mock, patch

from django.conf import settings
from django.test import TestCase

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
    @patch("platform_plugin_aspects.utils._generate_guest_token")
    def test_generate_superset_context(self, mock_generate_guest_token):
        """
        Test generate_superset_context
        """
        course_mock = Mock()
        filter_mock = Mock()
        user_mock = Mock()
        context = {"course": course_mock}
        dashboards = settings.ASPECTS_INSTRUCTOR_DASHBOARDS

        dashboards.append(
            {
                "slug": "test-slug",
                "uuid": "3ea6e738-989d-4325-8f93-82bb684dab5c",
                "allow_translations": False,
            }
        )

        mock_generate_guest_token.return_value = ("test-token", dashboards)

        context = generate_superset_context(
            context,
            user_mock,
            dashboards=dashboards,
            filters=[filter_mock],
            language="en_US",
        )

        self.assertEqual(context["superset_token"], "test-token")
        self.assertEqual(context["superset_dashboards"], dashboards)
        self.assertEqual(context["superset_url"], "http://superset-dummy-url/")
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
        user_mock = Mock()
        context = {"course": course_mock}
        mock_superset_client.side_effect = Exception("test-exception")

        context = generate_superset_context(
            context,
            user_mock,
            dashboards=[{"name": "test", "uuid": "test-dashboard-uuid"}],
            filters=[filter_mock],
        )

        self.assertIn("exception", context)

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
    def test_generate_superset_context_succesful(self, mock_superset_client):
        """
        Test generate_superset_context
        """
        course_mock = Mock()
        filter_mock = Mock()
        user_mock = Mock()
        user_mock.username = "test-user"
        context = {"course": course_mock}
        response_mock = Mock(status_code=200)
        mock_superset_client.return_value.session.post.return_value = response_mock
        response_mock.json.return_value = {
            "token": "test-token",
        }

        dashboards = [{"name": "test", "uuid": "test-dashboard-uuid"}]

        context = generate_superset_context(
            context,
            user_mock,
            dashboards=dashboards,
            filters=[filter_mock],
        )

        self.assertEqual(context["superset_token"], "test-token")
        self.assertEqual(context["superset_dashboards"], dashboards)
        self.assertEqual(context["superset_url"], "http://dummy-superset-url/")

    def test_generate_superset_context_with_exception(self):
        """
        Test generate_superset_context
        """
        course_mock = Mock()
        filter_mock = Mock()
        user_mock = Mock()
        user_mock.username = "test-user"
        context = {"course": course_mock}

        context = generate_superset_context(
            context,
            user_mock,
            dashboards=[{"name": "test", "uuid": "test-dashboard-uuid"}],
            filters=[filter_mock],
        )

        self.assertIn("exception", context)
