"""
platform_plugin_aspects Django application initialization.
"""

from django.apps import AppConfig
from edx_django_utils.plugins import PluginSettings, PluginSignals, PluginURLs


class PlatformPluginAspectsConfig(AppConfig):
    """
    Configuration for the aspects Django application.
    """

    name = "platform_plugin_aspects"

    plugin_app = {
        PluginURLs.CONFIG: {
            "lms.djangoapp": {
                PluginURLs.NAMESPACE: "",
                PluginURLs.REGEX: r"^aspects/",
                PluginURLs.RELATIVE_PATH: "urls",
            },
            "cms.djangoapp": {
                PluginURLs.NAMESPACE: "",
                PluginURLs.REGEX: r"^aspects/",
                PluginURLs.RELATIVE_PATH: "urls",
            },
        },
        PluginSettings.CONFIG: {
            "lms.djangoapp": {
                "production": {PluginSettings.RELATIVE_PATH: "settings.production"},
                "common": {PluginSettings.RELATIVE_PATH: "settings.common"},
            },
            "cms.djangoapp": {
                "production": {PluginSettings.RELATIVE_PATH: "settings.production"},
                "common": {PluginSettings.RELATIVE_PATH: "settings.common"},
            },
        },
        # Configuration setting for Plugin Signals for this app.
        PluginSignals.CONFIG: {
            # Configure the Plugin Signals for each Project Type, as needed.
            "cms.djangoapp": {
                # List of all plugin Signal receivers for this app and project type.
                PluginSignals.RECEIVERS: [
                    {
                        # The name of the app's signal receiver function.
                        PluginSignals.RECEIVER_FUNC_NAME: "receive_course_publish",
                        # The full path to the module where the signal is defined.
                        PluginSignals.SIGNAL_PATH: "xmodule.modulestore.django.COURSE_PUBLISHED",
                    }
                ],
            },
            "lms.djangoapp": {
                # List of all plugin Signal receivers for this app and project type.
                PluginSignals.RECEIVERS: [
                    {
                        # The name of the app's signal receiver function.
                        PluginSignals.RECEIVER_FUNC_NAME: "receive_course_enrollment_changed",
                        # The full path to the module where the signal is defined.
                        PluginSignals.SIGNAL_PATH: "common.djangoapps.student.signals.signals.ENROLL_STATUS_CHANGE",
                    }
                ],
            },
        },
    }

    def ready(self):
        """Load modules of Aspects."""
        super().ready()
        from platform_plugin_aspects import (  # pylint: disable=import-outside-toplevel, unused-import
            signals,
            sinks,
            tasks,
        )
        from platform_plugin_aspects.extensions import (  # pylint: disable=unused-import, import-outside-toplevel
            filters,
        )
