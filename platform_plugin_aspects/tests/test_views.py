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

from ..views import (
    DEFAULT_FILTERS_FORMAT,
    IsCourseStaffInstructor,
    SupersetInContextDashboardView,
    SupersetInstructorDashboardView,
    SupersetTokenView,
)

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
        self.superset_in_context_dashboard_course_url = (
            f"/superset_in_context_dashboard/{COURSE_ID}"
        )
        self.superset_in_context_dashboard_block_url = (
            "/superset_in_context_dashboard/"
            "block-v1:org+course+run+type@problem+block@e25d8eac15224f91bd3aa22bfe28a602"
        )
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
        mock_model_only = Mock(return_value=Mock(get=mock_model_get))
        mock_get_model.return_value = Mock(
            objects=Mock(only=mock_model_only),
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
        mock_model_only = Mock(return_value=Mock(get=mock_model_get))
        mock_get_model.return_value = Mock(
            objects=Mock(only=mock_model_only),
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
            dashboards=(
                settings.ASPECTS_INSTRUCTOR_DASHBOARDS
                + list(settings.ASPECTS_IN_CONTEXT_DASHBOARDS.values())
            ),
            filters=DEFAULT_FILTERS_FORMAT,
        )

    def test_in_context_dashboard_requires_authorization(self):
        response = self.client.get(self.superset_in_context_dashboard_course_url)
        self.assertEqual(response.status_code, 403)

    def test_in_context_dashboard_requires_course_access(self):
        self.client.login(username="user", password="password")
        response = self.client.get(self.superset_in_context_dashboard_course_url)
        self.assertEqual(response.status_code, 403)

    def test_in_context_dashboard_invalid_usage_key(self):
        # Will fail as it is not a well-formed block id.
        superset_in_context_dashboard_course_url = (
            "/superset_in_context_dashboard/block-v1:org+course+run"
        )
        self.client.login(username="user", password="password")
        response = self.client.get(superset_in_context_dashboard_course_url)
        self.assertEqual(response.status_code, 404)

    @patch("platform_plugin_aspects.views.get_model")
    def test_in_context_dashboard_course_not_found(self, mock_get_model):
        mock_model_get = Mock(side_effect=ObjectDoesNotExist)
        mock_model_only = Mock(return_value=Mock(get=mock_model_get))
        mock_get_model.return_value = Mock(
            objects=Mock(only=mock_model_only),
            DoesNotExist=ObjectDoesNotExist,
        )

        self.client.login(username="user", password="password")
        response = self.client.get(self.superset_in_context_dashboard_course_url)
        self.assertEqual(response.status_code, 404)
        mock_model_get.assert_called_once()

    @patch("platform_plugin_aspects.views.get_model")
    def test_in_context_dashboard_block_course_not_found(self, mock_get_model):
        mock_model_get = Mock(side_effect=ObjectDoesNotExist)
        mock_model_only = Mock(return_value=Mock(get=mock_model_get))
        mock_get_model.return_value = Mock(
            objects=Mock(only=mock_model_only),
            DoesNotExist=ObjectDoesNotExist,
        )

        self.client.login(username="user", password="password")
        response = self.client.get(self.superset_in_context_dashboard_block_url)
        self.assertEqual(response.status_code, 404)
        mock_model_get.assert_called_once()

    @patch.object(IsCourseStaffInstructor, "has_object_permission")
    def test_in_context_dashboard_block_no_dashboard(self, mock_has_object_permission):
        mock_has_object_permission.return_value = True
        # Will be not found as test settings do not include dashboard for video blocks.
        superset_in_context_dashboard_video_block_url = (
            "/superset_in_context_dashboard/"
            "block-v1:org+course+run+type@video+block@e25d8eac15224f91bd3aa22bfe28a602"
        )
        self.client.login(username="user", password="password")
        response = self.client.get(superset_in_context_dashboard_video_block_url)
        self.assertEqual(response.status_code, 404)

    @patch.object(IsCourseStaffInstructor, "has_object_permission")
    @patch("platform_plugin_aspects.views.get_localized_uuid")
    def test_in_context_dashboard_course(
        self, mock_get_localized_uuid, mock_has_object_permission
    ):
        mock_has_object_permission.return_value = True
        mock_get_localized_uuid.return_value = "00000000-0000-0000-0000-000000000000"

        self.client.login(username="user", password="password")
        response = self.client.get(self.superset_in_context_dashboard_course_url)

        mock_has_object_permission.assert_called_once()

        dashboard_uuid = settings.ASPECTS_IN_CONTEXT_DASHBOARDS["course"]["uuid"]
        mock_get_localized_uuid.assert_called_once_with(dashboard_uuid, "en")

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["dashboardId"], "00000000-0000-0000-0000-000000000000")
        self.assertEqual(data["defaultCourseRun"], "run")

    @patch.object(IsCourseStaffInstructor, "has_object_permission")
    @patch("platform_plugin_aspects.views.get_localized_uuid")
    def test_in_context_dashboard_block(
        self, mock_get_localized_uuid, mock_has_object_permission
    ):
        mock_has_object_permission.return_value = True
        mock_get_localized_uuid.return_value = "00000000-0000-0000-0000-000000000000"

        self.client.login(username="user", password="password")
        response = self.client.get(self.superset_in_context_dashboard_block_url)

        mock_has_object_permission.assert_called_once()

        dashboard_uuid = settings.ASPECTS_IN_CONTEXT_DASHBOARDS["problem"]["uuid"]
        mock_get_localized_uuid.assert_called_once_with(dashboard_uuid, "en")

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["dashboardId"], "00000000-0000-0000-0000-000000000000")
        self.assertEqual(data["defaultCourseRun"], "run")


class SupersetInstructorDashboardViewTestCase(TestCase):
    """
    Test cases for SupersetInstructorDashboardView.
    """

    def setUp(self):
        """
        Set up data used by multiple tests.
        """
        super().setUp()
        self.client = APIClient()
        self.url = f"/superset_instructor_dashboard/{COURSE_ID}"
        self.user = User.objects.create(
            username="instructor",
            email="instructor@example.com",
        )
        self.user.set_password("password")
        self.user.save()

    def test_requires_authorization(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 403)

    def test_requires_course_access(self):
        self.client.login(username="instructor", password="password")
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 403)

    def test_invalid_course_id(self):
        self.client.login(username="instructor", password="password")
        response = self.client.get(
            "/superset_instructor_dashboard/block-v1:org+course+run"
        )
        self.assertEqual(response.status_code, 404)

    @patch("platform_plugin_aspects.views.get_model")
    def test_course_not_found(self, mock_get_model):
        mock_model_get = Mock(side_effect=ObjectDoesNotExist)
        mock_model_only = Mock(return_value=Mock(get=mock_model_get))
        mock_get_model.return_value = Mock(
            objects=Mock(only=mock_model_only),
            DoesNotExist=ObjectDoesNotExist,
        )

        self.client.login(username="instructor", password="password")
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 404)
        mock_model_get.assert_called_once()

    @patch.object(IsCourseStaffInstructor, "has_object_permission")
    @patch("platform_plugin_aspects.views.generate_superset_context")
    def test_success(self, mock_generate_superset_context, mock_has_object_permission):
        mock_has_object_permission.return_value = True
        mock_generate_superset_context.return_value = {
            "course_id": COURSE_ID,
            "superset_dashboards": [
                {
                    "name": "Course Dashboard",
                    "uuid": "test-uuid",
                    "slug": "course-dashboard",
                }
            ],
            "superset_url": "https://superset.example.com",
            "superset_guest_token_url": f"https://lms.example.com/aspects/superset_guest_token/{COURSE_ID}",
        }

        self.client.login(username="instructor", password="password")
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("superset_dashboards", data)
        self.assertIn("superset_url", data)
        self.assertIn("superset_guest_token_url", data)
        self.assertIn("show_dashboard_link", data)
        self.assertEqual(data["superset_url"], "https://superset.example.com")
        mock_has_object_permission.assert_called_once()
        mock_generate_superset_context.assert_called_once()

    @patch.object(IsCourseStaffInstructor, "has_object_permission")
    @patch("platform_plugin_aspects.views.generate_superset_context")
    def test_show_dashboard_link_from_settings(
        self, mock_generate_superset_context, mock_has_object_permission
    ):
        mock_has_object_permission.return_value = True
        mock_generate_superset_context.return_value = {
            "course_id": COURSE_ID,
            "superset_dashboards": [],
            "superset_url": "https://superset.example.com",
            "superset_guest_token_url": f"https://lms.example.com/aspects/superset_guest_token/{COURSE_ID}",
        }

        self.client.login(username="instructor", password="password")
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(
            data["show_dashboard_link"],
            settings.SUPERSET_SHOW_INSTRUCTOR_DASHBOARD_LINK,
        )


PERMISSION_TEST_URLS = (
    f"/superset_guest_token/{COURSE_ID}",
    f"/superset_in_context_dashboard/{COURSE_ID}",
    (
        "/superset_in_context_dashboard/"
        "block-v1:org+course+run+type@problem+block@e25d8eac15224f91bd3aa22bfe28a602"
    ),
    f"/superset_instructor_dashboard/{COURSE_ID}",
)


@ddt.ddt
class ViewPermissionsTestCase(TestCase):
    """
    Test that only global staff or course staff/instructors can access the views.
    """

    def setUp(self):
        """
        Set up data used by multiple tests.

        The helpers are always given serializable return values: a bare
        MagicMock in a response sends DRF's JSON encoder into an endless
        tolist() chain, so a permission regression would exhaust memory
        instead of failing the assertion.
        """
        super().setUp()
        self.client = APIClient()
        self.mock_generate_guest_token = self._patch(
            "platform_plugin_aspects.views.generate_guest_token",
            return_value="test-token",
        )
        self.mock_generate_superset_context = self._patch(
            "platform_plugin_aspects.views.generate_superset_context",
            return_value={
                "superset_dashboards": [],
                "superset_url": "https://superset.example.com",
                "superset_guest_token_url": "https://lms.example.com/token",
            },
        )
        self._patch(
            "platform_plugin_aspects.views.get_localized_uuid",
            return_value="00000000-0000-0000-0000-000000000000",
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
        Assert the request was refused before any token or context was generated.
        """
        self.assertEqual(response.status_code, 403)
        self.mock_generate_guest_token.assert_not_called()
        self.mock_generate_superset_context.assert_not_called()

    @ddt.data(*PERMISSION_TEST_URLS)
    def test_global_staff_allowed(self, url):
        """
        Global staff can access every view without a course role.
        """
        self._login(is_staff=True)

        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)

    @ddt.data(*PERMISSION_TEST_URLS)
    def test_course_staff_allowed(self, url):
        """
        Course staff/instructors who are not global staff can access every view.
        """
        self._login()
        self._set_course_role(True)

        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)

    @ddt.data(*PERMISSION_TEST_URLS)
    def test_non_staff_denied(self, url):
        """
        Authenticated users with no staff or course role are denied.
        """
        self._login()
        self._set_course_role(False)

        self._assert_denied(self.client.get(url))

    @ddt.data(*PERMISSION_TEST_URLS)
    def test_non_staff_head_denied(self, url):
        """
        Safe methods other than GET do not bypass the staff check.
        """
        self._login()
        self._set_course_role(False)

        self._assert_denied(self.client.head(url))

    @ddt.data(*PERMISSION_TEST_URLS)
    def test_superuser_without_staff_denied(self, url):
        """
        IsAdminUser only checks is_staff, so a superuser without it is denied.
        """
        self._login(is_superuser=True)
        self._set_course_role(False)

        self._assert_denied(self.client.get(url))

    @ddt.data(
        SupersetTokenView,
        SupersetInContextDashboardView,
        SupersetInstructorDashboardView,
    )
    def test_permission_classes(self, view_class):
        """
        Guard against reintroducing a permission that allows any safe method.
        """
        is_authenticated, staff_or_course_staff = view_class.permission_classes
        self.assertIs(is_authenticated, permissions.IsAuthenticated)
        self.assertIs(staff_or_course_staff.op1_class, permissions.IsAdminUser)
        self.assertIs(staff_or_course_staff.op2_class, IsCourseStaffInstructor)
