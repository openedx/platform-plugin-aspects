"""
Test plugin settings
"""

from django.conf import settings
from django.test import TestCase

from platform_plugin_aspects.settings import common as common_settings
from platform_plugin_aspects.settings import production as production_setttings


class TestPluginSettings(TestCase):
    """
    Tests plugin settings
    """

    def test_common_settings(self):
        """
        Test common settings
        """
        common_settings.plugin_settings(settings)

        for key in ("url", "username", "password", "database", "timeout_secs"):
            assert key in settings.EVENT_SINK_CLICKHOUSE_BACKEND_CONFIG

    def test_production_settings(self):
        """
        Test production settings
        """
        test_url = "https://foo.bar"
        test_username = "bob"
        test_password = "secret"
        test_database = "cool_data"
        test_timeout = 1

        settings.ENV_TOKENS = {
            'EVENT_SINK_CLICKHOUSE_BACKEND_CONFIG': {
                "url": test_url,
                "username": test_username,
                "password": test_password,
                "database": test_database,
                "timeout_secs": test_timeout
            }
        }
        production_setttings.plugin_settings(settings)

        for key, val in (
            ("url", test_url),
            ("username", test_username),
            ("password", test_password),
            ("database", test_database),
            ("timeout_secs", test_timeout),
        ):
            assert key in settings.EVENT_SINK_CLICKHOUSE_BACKEND_CONFIG
            assert settings.EVENT_SINK_CLICKHOUSE_BACKEND_CONFIG[key] == val
