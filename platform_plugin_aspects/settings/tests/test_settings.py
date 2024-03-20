"""
Test plugin settings for commond, devstack and production environments
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
        settings.MAKO_TEMPLATE_DIRS_BASE = []
        common_settings.plugin_settings(settings)
        self.assertIn("MAKO_TEMPLATE_DIRS_BASE", settings.__dict__)
        self.assertIn("internal_service_url", settings.SUPERSET_CONFIG)
        self.assertNotIn("service_url", settings.SUPERSET_CONFIG)
        self.assertIn("username", settings.SUPERSET_CONFIG)
        self.assertIn("password", settings.SUPERSET_CONFIG)
        self.assertIsNotNone(settings.ASPECTS_INSTRUCTOR_DASHBOARDS)
        self.assertIsNotNone(settings.SUPERSET_EXTRA_FILTERS_FORMAT)
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
            "SUPERSET_CONFIG": {
                "internal_service_url": "http://superset:8088",
                "service_url": "http://superset.local.overhang.io",
                "username": "superset",
                "password": "superset",
            },
            "ASPECTS_INSTRUCTOR_DASHBOARDS": [
                {
                    "name": "Instructor Dashboard",
                    "uuid": "test-settings-dashboard-uuid",
                }
            ],
            "SUPERSET_EXTRA_FILTERS_FORMAT": [],
            "EVENT_SINK_CLICKHOUSE_BACKEND_CONFIG": {
                "url": test_url,
                "username": test_username,
                "password": test_password,
                "database": test_database,
                "timeout_secs": test_timeout,
            },
        }
        production_setttings.plugin_settings(settings)
        self.assertEqual(
            settings.SUPERSET_CONFIG, settings.ENV_TOKENS["SUPERSET_CONFIG"]
        )
        self.assertEqual(
            settings.ASPECTS_INSTRUCTOR_DASHBOARDS,
            settings.ENV_TOKENS["ASPECTS_INSTRUCTOR_DASHBOARDS"],
        )
        self.assertEqual(
            settings.SUPERSET_EXTRA_FILTERS_FORMAT,
            settings.ENV_TOKENS["SUPERSET_EXTRA_FILTERS_FORMAT"],
        )

        for key, val in (
            ("url", test_url),
            ("username", test_username),
            ("password", test_password),
            ("database", test_database),
            ("timeout_secs", test_timeout),
        ):
            assert key in settings.EVENT_SINK_CLICKHOUSE_BACKEND_CONFIG
            assert settings.EVENT_SINK_CLICKHOUSE_BACKEND_CONFIG[key] == val
