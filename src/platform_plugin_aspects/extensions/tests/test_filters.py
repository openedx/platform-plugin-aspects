"""
Tests for the filters module.
"""

from unittest.mock import Mock, patch

from django.test import TestCase

from platform_plugin_aspects.extensions.filters import (
    BLOCK_CATEGORY,
    AddSupersetTab,
    AddSupersetTabToInstructorDashboard,
)


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

    @patch("platform_plugin_aspects.extensions.filters.get_user_dashboard_locale")
    def test_run_filter(
        self,
        mock_get_user_dashboard_locale,
    ):
        """
        Check the filter is not executed when there are no LimeSurvey blocks in the course.

        Expected result:
            - The context is returned without modifications.
        """
        mock_get_user_dashboard_locale.return_value = "en"

        context = self.filter.run_filter(self.context, self.template_name)

        assert {
            "course_id": self.course_id,
            "section_key": BLOCK_CATEGORY,
            "section_display_name": "Reports",
            "superset_url": "http://superset-dummy-url/",
            "superset_guest_token_url": f"https://lms.url/superset_guest_token/{self.course_id}",
            "template_path_prefix": "/instructor_dashboard/",
        }.items() <= context["context"]["sections"][0].items()

        mock_get_user_dashboard_locale.assert_called_once()


class TestAddSupersetTabToInstructorDashboard(TestCase):
    """
    Test suite for the AddSupersetTabToInstructorDashboard filter.
    """

    def setUp(self) -> None:
        """
        Set up the test suite.
        """
        self.filter = AddSupersetTabToInstructorDashboard(
            filter_type=Mock(), running_pipeline=Mock()
        )
        self.course_key = Mock(__str__=Mock(return_value="course-v1:org+course+run"))
        self.user = Mock()

    def test_run_filter_appends_aspects_tab(self):
        """
        Check that the filter appends the Aspects tab to the existing tabs list.

        Expected result:
            - The returned tabs list contains the original tabs plus the new aspects tab.
        """
        existing_tab = {"tab_id": "existing", "title": "Existing", "sort_order": 10}
        tabs = [existing_tab]

        result = self.filter.run_filter(
            tabs=tabs, user=self.user, course_key=self.course_key
        )

        assert len(result["tabs"]) == 2
        aspects_tab = result["tabs"][1]
        assert aspects_tab["tab_id"] == "aspects"
        assert aspects_tab["title"] == "Reports"
        assert (
            aspects_tab["url"]
            == "/instructor-dashboard/course-v1:org+course+run/aspects/"
        )
        assert aspects_tab["sort_order"] == 120

    def test_run_filter_does_not_mutate_original_tabs(self):
        """
        Check that the filter does not modify the original tabs list.

        Expected result:
            - The original tabs list is unchanged after the filter runs.
        """
        original_tabs = [{"tab_id": "existing", "title": "Existing", "sort_order": 10}]
        tabs_copy = original_tabs.copy()

        self.filter.run_filter(
            tabs=original_tabs, user=self.user, course_key=self.course_key
        )

        assert original_tabs == tabs_copy

    def test_run_filter_with_empty_tabs(self):
        """
        Check that the filter works when the initial tabs list is empty.

        Expected result:
            - The returned tabs list contains only the aspects tab.
        """
        result = self.filter.run_filter(
            tabs=[], user=self.user, course_key=self.course_key
        )

        assert len(result["tabs"]) == 1
        assert result["tabs"][0]["tab_id"] == "aspects"
