"""
Endpoints for the Aspects platform plugin.
"""

from collections import namedtuple

import prison
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from opaque_keys import InvalidKeyError
from opaque_keys.edx.keys import CourseKey, UsageKey
from rest_framework import permissions
from rest_framework.authentication import SessionAuthentication
from rest_framework.exceptions import APIException, NotFound
from rest_framework.generics import GenericAPIView
from rest_framework.response import Response

from .utils import (
    DEFAULT_FILTERS_FORMAT,
    _,
    build_filter,
    generate_guest_token,
    get_localized_uuid,
    get_model,
    get_user_dashboard_locale,
)

try:
    from openedx.core.lib.api.permissions import (
        IsCourseStaffInstructor,
        IsStaffOrReadOnly,
    )
except ImportError:

    class IsCourseStaffInstructor(permissions.BasePermission):
        """
        Permission class to use during tests.

        Importing from edx-platform doesn't work when running tests,
        so we declare our own permission class here.
        """

        def has_object_permission(self, request, view, obj):
            """
            Return False for security; mock this out during tests.
            """
            return False

    class IsStaffOrReadOnly(permissions.BasePermission):
        """
        Permission class to use during tests.

        Importing from edx-platform doesn't work when running tests,
        so we declare our own permission class here.
        """

        def has_object_permission(self, request, view, obj):
            """
            Return False for security; mock this out during tests.
            """
            return False


# Course fields:
# * course_id: CourseKey; required by IsCourseStaffInstructor
# * display_name: str; optionally fetched from CourseOverview
Course = namedtuple("Course", ["course_id", "display_name"])


def _get_course(course_key):
    """
    Return a Course-like object for the requested course id.

    Raise NotFound if the corresponding course does not exist.
    """
    # Fetch the CourseOverview (if we're running in edx-platform)
    display_name = ""
    CourseOverview = get_model("course_overviews")
    if CourseOverview:
        try:
            course_overview = CourseOverview.objects.only("display_name").get(
                id=course_key
            )
            display_name = course_overview.display_name
        except CourseOverview.DoesNotExist as exc:
            raise NotFound(
                _("Course not found: '{course_id}'").format(course_id=course_key)
            ) from exc
    return Course(course_id=course_key, display_name=display_name)


class SupersetTokenView(GenericAPIView):
    """
    Superset guest token endpoint.
    """

    authentication_classes = (SessionAuthentication,)
    permission_classes = (
        permissions.IsAuthenticated,
        IsStaffOrReadOnly | IsCourseStaffInstructor,
    )

    lookup_field = "course_id"

    def get_object(self):
        """
        Return a Course-like object for the requested course_id.
        """
        course_id = self.kwargs.get(self.lookup_field, "")
        try:
            course_key = CourseKey.from_string(course_id)
        except InvalidKeyError as exc:
            raise NotFound(
                _("Invalid course id: '{course_id}'").format(course_id=course_id)
            ) from exc

        course = _get_course(course_key)

        # May raise a permission denied
        self.check_object_permissions(self.request, course)

        return course_key

    def get(self, request, *args, **kwargs):
        """
        Return a guest token for accessing the Superset API.
        """
        course = self.get_object()

        dashboards = settings.ASPECTS_INSTRUCTOR_DASHBOARDS.copy()

        # Only include these dashboards if in-context metrics are on,
        # otherwise this call will always fail in older releases without
        # admin intervention. This can be removed when we stop supporting
        # < Sumac.
        if settings.ASPECTS_ENABLE_STUDIO_IN_CONTEXT_METRICS:
            dashboards.extend(settings.ASPECTS_IN_CONTEXT_DASHBOARDS.values())

        extra_filters_format = settings.SUPERSET_EXTRA_FILTERS_FORMAT

        try:
            guest_token = generate_guest_token(
                user=request.user,
                course=course,
                dashboards=dashboards,
                filters=DEFAULT_FILTERS_FORMAT + extra_filters_format,
            )
        except ImproperlyConfigured as exc:
            raise APIException() from exc

        return Response({"guestToken": guest_token})


class SupersetInContextDashboardView(GenericAPIView):
    """
    Endpoint for in-context analytics embedded Superset dashboard parameters.
    """

    authentication_classes = (SessionAuthentication,)
    permission_classes = (
        permissions.IsAuthenticated,
        IsStaffOrReadOnly | IsCourseStaffInstructor,
    )

    lookup_field = "usage_id"

    def get_object(self):
        """
        Return a usage key or course key for the requested usage_key.
        """
        usage_id = self.kwargs.get(self.lookup_field, "")
        try:
            usage_key = UsageKey.from_string(usage_id)
        except InvalidKeyError as exc:
            try:
                course_key = usage_key = CourseKey.from_string(usage_id)
            except InvalidKeyError:
                raise NotFound(
                    _("Invalid usage id: '{usage_id}'").format(usage_id=usage_id)
                ) from exc
        else:
            course_key = usage_key.course_key

        course = _get_course(course_key)
        self.check_object_permissions(self.request, course)

        return usage_key

    def get(self, request, *args, **kwargs):
        """
        Return Superset context for embedding the dashboard for the requested block.
        """
        usage_key = self.get_object()
        if isinstance(usage_key, CourseKey):
            block_type = "course"
            course_key = usage_key
        else:
            block_type = usage_key.block_type
            course_key = usage_key.course_key

        course_key_col = settings.IN_CONTEXT_DASHBOARD_COURSE_KEY_COLUMN
        block_id_col = settings.IN_CONTEXT_DASHBOARD_BLOCK_ID_COLUMN

        dashboards = settings.ASPECTS_IN_CONTEXT_DASHBOARDS
        dashboard = dashboards.get(block_type)
        if dashboard is None:
            raise NotFound(
                _("No dashboard for block type: '{block_type}'").format(
                    block_type=block_type
                )
            )

        block_filter = {}
        if not isinstance(usage_key, CourseKey):
            for filter_id in dashboard["block_filter_ids"]:
                block_filter[filter_id] = build_filter(
                    filter_id, block_id_col, "IN", [usage_key.block_id]
                )

        course_runs = {}
        # In the future we might provide other course runs so that the
        # embedding application can apply their corresponding filters
        # instead of needing the Superset filter UI.
        for course_run in [course_key.run]:
            course_filter = block_filter.copy()
            for filter_id in dashboard["course_filter_ids"]:
                course_filter[filter_id] = build_filter(
                    filter_id, course_key_col, "IN", [str(course_key)]
                )
            course_runs[course_run] = {
                # Superset filter URL parameter is encoded as Rison.
                "native_filters": prison.dumps(course_filter),
            }

        if dashboard.get("allow_translations"):
            language = get_user_dashboard_locale(request.user)
            dashboard = dashboard.copy()
            dashboard["uuid"] = get_localized_uuid(dashboard["uuid"], language)

        superset_config = settings.SUPERSET_CONFIG
        superset_url = superset_config.get("service_url")

        return Response(
            {
                "dashboardId": dashboard["uuid"],
                "supersetUrl": superset_url,
                "courseRuns": course_runs,
                "defaultCourseRun": course_key.run,
            }
        )
