"""
Tests for the filters module.
"""

from unittest.mock import Mock, patch

from django.test import TestCase

from platform_plugin_aspects.extensions.filters import BLOCK_CATEGORY, AddSupersetTab


class TestFilters(TestCase):
    """
    Test suite for the LimeSurveyXBlock filters.
    """

    def setUp(self) -> None:
        """
        Set up the test suite.
        """
        self.filter = AddSupersetTab(filter_type=Mock(), running_pipeline=Mock())
        self.template_name = "test-template-name"
        self.course_id = "course-v1:org+course+run"
        self.context = {"course": Mock(id=self.course_id), "sections": []}

    @patch("platform_plugin_aspects.extensions.filters.get_model")
    def test_run_filter_with_language(
        self,
        mock_get_model,
    ):
        """
        Check the filter is not executed when there are no LimeSurvey blocks in the course.

        Expected result:
            - The context is returned without modifications.
        """
        mock_get_model.return_value.get_value.return_value = "not-a-language"

        context = self.filter.run_filter(self.context, self.template_name)

        self.assertDictContainsSubset(
            {
                "course_id": self.course_id,
                "section_key": BLOCK_CATEGORY,
                "section_display_name": "Analytics",
                "superset_url": "http://superset-dummy-url/",
                "superset_guest_token_url": f"https://lms.url/superset_guest_token/{self.course_id}",
                "template_path_prefix": "/instructor_dashboard/",
            },
            context["context"]["sections"][0],
        )
        mock_get_model.assert_called_once()

    @patch("platform_plugin_aspects.extensions.filters.get_model")
    def test_run_filter_without_language(
        self,
        mock_get_model,
    ):
        """
        Check the filter is not executed when there are no LimeSurvey blocks in the course.

        Expected result:
            - The context is returned without modifications.
        """
        mock_get_model.return_value.get_value.return_value = None

        context = self.filter.run_filter(self.context, self.template_name)

        self.assertDictContainsSubset(
            {
                "course_id": self.course_id,
                "section_key": BLOCK_CATEGORY,
                "section_display_name": "Analytics",
                "superset_url": "http://superset-dummy-url/",
                "superset_guest_token_url": f"https://lms.url/superset_guest_token/{self.course_id}",
                "template_path_prefix": "/instructor_dashboard/",
            },
            context["context"]["sections"][0],
        )

        mock_get_model.assert_called_once()
