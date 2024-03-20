"""
Common Django settings for eox_hooks project.
For more information on this file, see
https://docs.djangoproject.com/en/2.22/topics/settings/
For the full list of settings and their values, see
https://docs.djangoproject.com/en/2.22/ref/settings/
"""

from platform_plugin_aspects import ROOT_DIRECTORY


def plugin_settings(settings):
    """
    Set of plugin settings used by the Open Edx platform.
    More info: https://github.com/edx/edx-platform/blob/master/openedx/core/djangoapps/plugins/README.rst
    """
    settings.MAKO_TEMPLATE_DIRS_BASE.append(ROOT_DIRECTORY / "templates")
    settings.SUPERSET_CONFIG = {
        "internal_service_url": "http://superset:8088",
        "username": "superset",
        "password": "superset",
    }
    settings.ASPECTS_INSTRUCTOR_DASHBOARDS = [
        {
            "name": "Instructor Dashboard",
            "uuid": "1d6bf904-f53f-47fd-b1c9-6cd7e284d286",
        },
    ]
    settings.SUPERSET_EXTRA_FILTERS_FORMAT = []
    settings.EVENT_SINK_CLICKHOUSE_BACKEND_CONFIG = {
        # URL to a running ClickHouse server's HTTP interface. ex: https://foo.openedx.org:8443/ or
        # http://foo.openedx.org:8123/ . Note that we only support the ClickHouse HTTP interface
        # to avoid pulling in more dependencies to the platform than necessary.
        "url": "http://clickhouse:8123",
        "username": "ch_cms",
        "password": "password",
        "database": "event_sink",
        "timeout_secs": 5,
    }

    settings.EVENT_SINK_CLICKHOUSE_PII_MODELS = [
        "user_profile",
        "external_id",
    ]

    settings.EVENT_SINK_CLICKHOUSE_MODEL_CONFIG = {
        "auth_user": {
            "module": "django.contrib.auth.models",
            "model": "User",
        },
        "user_profile": {
            "module": "common.djangoapps.student.models",
            "model": "UserProfile",
        },
        "course_overviews": {
            "module": "openedx.core.djangoapps.content.course_overviews.models",
            "model": "CourseOverview",
        },
        "external_id": {
            "module": "openedx.core.djangoapps.external_user_ids.models",
            "model": "ExternalId",
        },
        "custom_course_edx": {
            "module": "lms.djangoapps.ccx.models",
            "model": "CustomCourseForEdX",
        },
    }
