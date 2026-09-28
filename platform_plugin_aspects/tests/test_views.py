"""
Test views.
"""

from unittest.mock import Mock, patch

import ddt
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.exceptions import ImproperlyConfigured, ObjectDoesNotExist
from django.test import TestCase
from opaque_keys.edx.keys import CourseKey
from rest_framework import permissions
from rest_framework.test import APIClient

from ..views import DEFAULT_FILTERS_FORMAT, IsCourseStaffInstructor, SupersetView

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


@ddt.ddt
class ViewPermissionsTestCase(TestCase):
    """
    Test that only global staff or course staff/instructors can access the view.
    """

    def setUp(self):
        """
        Set up data used by multiple tests.

        The guest token is always given a serializable return value: a bare
        MagicMock in a response sends DRF's JSON encoder into an endless
        tolist() chain, so a permission regression would exhaust memory
        instead of failing the assertion.
        """
        super().setUp()
        self.client = APIClient()
        self.url = f"/superset_guest_token/{COURSE_ID}"
        self.mock_generate_guest_token = self._patch(
            "platform_plugin_aspects.views.generate_guest_token",
            return_value="test-token",
        )

    def _patch(self, target, **kwargs):
        """
        Patch target for the duration of the test and return the mock.
        """
        patcher = patch(target, **kwargs)
        self.addCleanup(patcher.stop)
        return patcher.start()

    def _login(self, **user_kwargs):
        """
        Create a user with the given attributes and log them in.
        """
        user = User.objects.create(username="user", **user_kwargs)
        user.set_password("password")
        user.save()
        self.client.login(username="user", password="password")
        return user

    def _set_course_role(self, has_role):
        """
        Mock whether the user is course staff or an instructor.
        """
        self._patch(
            "platform_plugin_aspects.views.IsCourseStaffInstructor.has_object_permission",
            return_value=has_role,
        )

    def _assert_denied(self, response):
        """
        Assert the request was refused before any guest token was generated.
        """
        self.assertEqual(response.status_code, 403)
        self.mock_generate_guest_token.assert_not_called()

    def test_global_staff_allowed(self):
        """
        Global staff can get a guest token without a course role.
        """
        self._login(is_staff=True)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json().get("guestToken"), "test-token")

    def test_course_staff_allowed(self):
        """
        Course staff/instructors who are not global staff can get a guest token.
        """
        self._login()
        self._set_course_role(True)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json().get("guestToken"), "test-token")

    @ddt.data("get", "head")
    def test_non_staff_denied(self, method):
        """
        Authenticated users with no staff or course role are denied, including
        for safe methods other than GET.
        """
        self._login()
        self._set_course_role(False)

        self._assert_denied(getattr(self.client, method)(self.url))

    def test_superuser_without_staff_denied(self):
        """
        IsAdminUser only checks is_staff, so a superuser without it is denied.
        """
        self._login(is_superuser=True)
        self._set_course_role(False)

        self._assert_denied(self.client.get(self.url))

    def test_permission_classes(self):
        """
        Guard against reintroducing a permission that allows any safe method.
        """
        is_authenticated, staff_or_course_staff = SupersetView.permission_classes
        self.assertIs(is_authenticated, permissions.IsAuthenticated)
        self.assertIs(staff_or_course_staff.op1_class, permissions.IsAdminUser)
        self.assertIs(staff_or_course_staff.op2_class, IsCourseStaffInstructor)
