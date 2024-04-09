"""
Production Django settings for Aspects project.
"""


def plugin_settings(settings):
    """
    Set of plugin settings used by the Open Edx platform.
    More info: https://github.com/edx/edx-platform/blob/master/openedx/core/djangoapps/plugins/README.rst
    """
    settings.SUPERSET_CONFIG = getattr(settings, "ENV_TOKENS", {}).get(
        "SUPERSET_CONFIG", settings.SUPERSET_CONFIG
    )
    settings.ASPECTS_INSTRUCTOR_DASHBOARDS = getattr(settings, "ENV_TOKENS", {}).get(
        "ASPECTS_INSTRUCTOR_DASHBOARDS", settings.ASPECTS_INSTRUCTOR_DASHBOARDS
    )
    settings.SUPERSET_EXTRA_FILTERS_FORMAT = getattr(settings, "ENV_TOKENS", {}).get(
        "SUPERSET_EXTRA_FILTERS_FORMAT", settings.SUPERSET_EXTRA_FILTERS_FORMAT
    )
    settings.SUPERSET_DASHBOARD_LOCALES = getattr(settings, "ENV_TOKENS", {}).get(
        "SUPERSET_DASHBOARD_LOCALES", settings.SUPERSET_DASHBOARD_LOCALES
    )
    settings.EVENT_SINK_CLICKHOUSE_BACKEND_CONFIG = settings.ENV_TOKENS.get(
        "EVENT_SINK_CLICKHOUSE_BACKEND_CONFIG",
        settings.EVENT_SINK_CLICKHOUSE_BACKEND_CONFIG,
    )
    settings.EVENT_SINK_CLICKHOUSE_PII_MODELS = settings.ENV_TOKENS.get(
        "EVENT_SINK_CLICKHOUSE_PII_MODELS",
        settings.EVENT_SINK_CLICKHOUSE_PII_MODELS,
    )
