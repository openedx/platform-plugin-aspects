"""
Test views.
"""

from unittest.mock import Mock, patch

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.exceptions import ImproperlyConfigured, ObjectDoesNotExist
from django.test import TestCase
from opaque_keys.edx.keys import CourseKey
from rest_framework.test import APIClient

from ..views import DEFAULT_FILTERS_FORMAT, IsCourseStaffInstructor

COURSE_ID = "course-v1:org+course+run"
User = get_user_model()


class ViewsTestCase(TestCase):
    """
    Test cases for the plugin views and URLs.
    """

    def setUp(self):
        """
        Set up data used by multiple tests.
        """
        super().setUp()
        self.client = APIClient()
        self.superset_guest_token_url = f"/superset_guest_token/{COURSE_ID}"
        self.user = User.objects.create(
            username="user",
            email="user@example.com",
        )
        self.user.set_password("password")
        self.user.save()

    def test_guest_token_requires_authorization(self):
        response = self.client.get(self.superset_guest_token_url)
        self.assertEqual(response.status_code, 403)

    def test_guest_token_requires_course_access(self):
        self.client.login(username="user", password="password")
        response = self.client.get(self.superset_guest_token_url)
        self.assertEqual(response.status_code, 403)

    def test_guest_token_invalid_course_id(self):
        superset_guest_token_url = "/superset_guest_token/block-v1:org+course+run"
        self.client.login(username="user", password="password")
        response = self.client.get(superset_guest_token_url)
        self.assertEqual(response.status_code, 404)

    @patch("platform_plugin_aspects.views.get_model")
    def test_guest_token_course_not_found(self, mock_get_model):
        mock_model_get = Mock(side_effect=ObjectDoesNotExist)
        mock_get_model.return_value = Mock(
            objects=Mock(get=mock_model_get),
            DoesNotExist=ObjectDoesNotExist,
        )

        self.client.login(username="user", password="password")
        response = self.client.get(self.superset_guest_token_url)
        self.assertEqual(response.status_code, 404)
        mock_model_get.assert_called_once()

    @patch.object(IsCourseStaffInstructor, "has_object_permission")
    @patch("platform_plugin_aspects.views.generate_guest_token")
    def test_guest_token(self, mock_generate_guest_token, mock_has_object_permission):
        mock_has_object_permission.return_value = True
        mock_generate_guest_token.return_value = "test-token"

        self.client.login(username="user", password="password")
        response = self.client.get(self.superset_guest_token_url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json().get("guestToken"), "test-token")
        mock_has_object_permission.assert_called_once()
        mock_generate_guest_token.assert_called_once()

    @patch.object(IsCourseStaffInstructor, "has_object_permission")
    @patch("platform_plugin_aspects.views.generate_guest_token")
    def test_no_guest_token(
        self, mock_generate_guest_token, mock_has_object_permission
    ):
        mock_has_object_permission.return_value = True
        mock_generate_guest_token.side_effect = ImproperlyConfigured

        self.client.login(username="user", password="password")
        response = self.client.get(self.superset_guest_token_url)

        self.assertEqual(response.status_code, 500)
        mock_has_object_permission.assert_called_once()
        mock_generate_guest_token.assert_called_once()

    @patch("platform_plugin_aspects.views.get_model")
    @patch.object(IsCourseStaffInstructor, "has_object_permission")
    @patch("platform_plugin_aspects.views.generate_guest_token")
    def test_guest_token_with_course_overview(
        self, mock_generate_guest_token, mock_has_object_permission, mock_get_model
    ):
        mock_has_object_permission.return_value = True
        mock_generate_guest_token.return_value = "test-token"
        mock_model_get = Mock(return_value=Mock(display_name="Course Title"))
        mock_get_model.return_value = Mock(
            objects=Mock(get=mock_model_get),
            DoesNotExist=ObjectDoesNotExist,
        )

        self.client.login(username="user", password="password")
        response = self.client.get(self.superset_guest_token_url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json().get("guestToken"), "test-token")
        mock_has_object_permission.assert_called_once()
        mock_model_get.assert_called_once()
        mock_generate_guest_token.assert_called_once_with(
            user=self.user,
            course=CourseKey.from_string(COURSE_ID),
            dashboards=settings.ASPECTS_INSTRUCTOR_DASHBOARDS,
            filters=DEFAULT_FILTERS_FORMAT,
        )
