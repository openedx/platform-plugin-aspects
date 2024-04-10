"""
Test views.
"""

from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

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
        """
        Unauthenticated hits to the endpoint redirect to login.
        """
        response = self.client.post(self.superset_guest_token_url)
        self.assertEqual(response.status_code, 302)
        self.assertIn("login", response.url)

    @patch("platform_plugin_aspects.views.generate_guest_token")
    def test_guest_token(self, mock_generate_guest_token):
        mock_generate_guest_token.return_value = ("test-token", "test-dashboard-uuid")
        self.client.login(username="user", password="password")
        response = self.client.post(self.superset_guest_token_url, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json().get("guestToken"), "test-token")
        mock_generate_guest_token.assert_called_once()
