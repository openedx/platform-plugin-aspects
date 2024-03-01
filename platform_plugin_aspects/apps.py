"""
platform_plugin_aspects Django application initialization.
"""

from django.apps import AppConfig


class PlatformPluginAspectsConfig(AppConfig):
    """
    Configuration for the aspects Django application.
    """

    name = "platform_plugin_aspects"

    plugin_app = {
        "settings_config": {
            "lms.djangoapp": {
                "common": {"relative_path": "settings.common"},
                "production": {"relative_path": "settings.production"},
            },
            "cms.djangoapp": {
                "common": {"relative_path": "settings.common"},
                "production": {"relative_path": "settings.production"},
            },
        },
    }

    def ready(self):
        """Load modules of Aspects."""
        from platform_plugin_aspects.extensions import filters  # pylint: disable=unused-import, import-outside-toplevel
