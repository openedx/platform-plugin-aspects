"""
Urls for the Aspects plugin.
"""

from django.urls import include, path, re_path

from . import views

# Copied from openedx.core.constants
COURSE_ID_PATTERN = r"(?P<course_id>[^/+]+(/|\+)[^/+]+(/|\+)[^/?]+)"
# Copied from lms.envs.common
USAGE_ID_PATTERN = (
    r"(?P<usage_id>(?:i4x://?[^/]+/[^/]+/[^/]+/[^@]+(?:@[^/]+)?)|(?:[^/]+))"
)

app_url_patterns = (
    [
        re_path(
            rf"superset_guest_token/{COURSE_ID_PATTERN}/?$",
            views.SupersetTokenView.as_view(),
            name="superset_guest_token",
        ),
        re_path(
            rf"superset_in_context_dashboard/{USAGE_ID_PATTERN}/?$",
            views.SupersetInContextDashboardView.as_view(),
            name="superset_in_context_dashboard",
        ),
    ],
    "platform_plugin_aspects",
)

urlpatterns = [
    path("", include(app_url_patterns)),
]
