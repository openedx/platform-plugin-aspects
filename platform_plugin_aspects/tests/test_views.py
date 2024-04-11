"""
Test views.
"""

from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient

from ..views import IsCourseStaffInstructor

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
        self.superset_guest_token_url = reverse(
            "superset_guest_token",
            kwargs={"course_id": COURSE_ID},
        )
        self.user = User.objects.create(
            username="user",
            email="user@example.com",
        )
        self.user.set_password("password")
        self.user.save()

    def test_guest_token_requires_authorization(self):
        response = self.client.post(self.superset_guest_token_url)
        self.assertEqual(response.status_code, 403)

    def test_guest_token_requires_course_access(self):
        self.client.login(username="user", password="password")
        response = self.client.post(self.superset_guest_token_url)
        self.assertEqual(response.status_code, 403)

    @patch.object(IsCourseStaffInstructor, "has_object_permission")
    @patch("platform_plugin_aspects.views.generate_guest_token")
    def test_guest_token(self, mock_generate_guest_token, mock_has_object_permission):
        mock_has_object_permission.return_value = True
        mock_generate_guest_token.return_value = ("test-token", "test-dashboard-uuid")

        self.client.login(username="user", password="password")
        response = self.client.post(self.superset_guest_token_url)
        mock_has_object_permission.assert_called_once()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json().get("guestToken"), "test-token")
        mock_generate_guest_token.assert_called_once()
