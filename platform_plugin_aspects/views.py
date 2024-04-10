"""
Endpoints for the Aspects platform plugin.
"""

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ImproperlyConfigured
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from opaque_keys.edx.keys import CourseKey

from .utils import _, generate_guest_token


@require_POST
@login_required
def superset_guest_token(request, course_id):
    """
    Return a guest token for Superset that the given request.user can use to access the Superset API.
    """
    # TODO -- restrict access to course staff? how?

    course_key = CourseKey.from_string(course_id)
    built_in_filters = [
        f"org = '{course_key.org}'",
        # TODO? Need to fetch the Course object to add this filter.
        # f"course_name = '{course_key.display_name}'",
        f"course_run = '{course_key.run}'",
    ]
    dashboards = settings.ASPECTS_INSTRUCTOR_DASHBOARDS
    extra_filters_format = settings.SUPERSET_EXTRA_FILTERS_FORMAT

    guest_token, exception = generate_guest_token(
        user=request.user,
        course=course_id,
        dashboards=dashboards,
        filters=built_in_filters + extra_filters_format,
    )

    if not guest_token:
        raise ImproperlyConfigured(
            _(
                "Unable to fetch Superset guest token, "
                "mostly likely due to invalid settings.SUPERSET_CONFIG: {exception}"
            ).format(exception=exception)
        )

    return JsonResponse({"guestToken": guest_token})
