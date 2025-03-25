"""
Urls for the Aspects plugin.
"""

from django.conf import settings
from django.urls import include, path, re_path

from . import views

# Copied from openedx.core.constants
COURSE_ID_PATTERN = r"(?P<course_id>[^/+]+(/|\+)[^/+]+(/|\+)[^/?]+)"

app_url_patterns = (
    [
        re_path(
            rf"superset_guest_token/{COURSE_ID_PATTERN}/?$",
            views.SupersetTokenView.as_view(),
            name="superset_guest_token",
        ),
        re_path(
            rf"superset_embedded_dashboard/{settings.USAGE_KEY_PATTERN}/?$",
            views.SupersetEmbeddedDashboardView.as_view(),
            name="superset_embedded_dashboard$",
        ),
    ],
    "platform_plugin_aspects",
)

urlpatterns = [
    path("", include(app_url_patterns)),
]
