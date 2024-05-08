"""
Endpoints for the Aspects platform plugin.
"""

from collections import namedtuple

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from opaque_keys import InvalidKeyError
from opaque_keys.edx.keys import CourseKey
from rest_framework import permissions
from rest_framework.authentication import SessionAuthentication
from rest_framework.exceptions import APIException, NotFound
from rest_framework.generics import GenericAPIView
from rest_framework.response import Response

from .utils import DEFAULT_FILTERS_FORMAT, _, generate_guest_token, get_model

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


class SupersetView(GenericAPIView):
    """
    Superset-related endpoints provided by the aspects platform plugin.
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

        # Fetch the CourseOverview (if we're running in edx-platform)
        display_name = ""
        CourseOverview = get_model("course_overviews")
        if CourseOverview:
            try:
                course_overview = CourseOverview.objects.get(id=course_key)
                display_name = course_overview.display_name
            except CourseOverview.DoesNotExist as exc:
                raise NotFound(
                    _("Course not found: '{course_id}'").format(course_id=course_id)
                ) from exc

        course = Course(course_id=course_key, display_name=display_name)

        # May raise a permission denied
        self.check_object_permissions(self.request, course)

        return course_key

    def get(self, request, *args, **kwargs):
        """
        Return a guest token for accessing the Superset API.
        """
        course = self.get_object()

        dashboards = settings.ASPECTS_INSTRUCTOR_DASHBOARDS
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
