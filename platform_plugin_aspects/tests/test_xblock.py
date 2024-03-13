#!/usr/bin/env python
"""
Test basic SupersetXBlock display function
"""
from unittest import TestCase
from unittest.mock import Mock, patch

from opaque_keys.edx.locator import CourseLocator
from xblock.field_data import DictFieldData
from xblock.reference.user_service import XBlockUser

from ..xblock import SupersetXBlock


def make_an_xblock(user_role, **kwargs):
    """
    Helper method that creates a new SupersetXBlock
    """
    course_id = CourseLocator("foo", "bar", "baz")
    mock_user = Mock(
        spec=XBlockUser,
        opt_attrs={
            "edx-platform.username": user_role,
            "edx-platform.user_role": user_role,
        },
    )

    def service(block, service):  # pylint: disable=unused-argument
        # Mock the user service
        if service == "user":
            return Mock(get_current_user=Mock(return_value=mock_user))
        # Mock the i18n service
        return Mock(_catalog={})

    def local_resource_url(_self, url):
        return url

    runtime = Mock(
        course_id=course_id,
        service=service,
        local_resource_url=Mock(side_effect=local_resource_url),
    )
    scope_ids = Mock()
    field_data = DictFieldData(kwargs)
    xblock = SupersetXBlock(runtime, field_data, scope_ids)
    xblock.xmodule_runtime = runtime
    return xblock


class TestRender(TestCase):
    """
    Test the HTML rendering of the XBlock
    """

    @patch("platform_plugin_aspects.utils.SupersetClient")
    def test_render_instructor(self, mock_superset_client):
        """
        Ensure staff can see the Superset dashboard.
        """
        mock_superset_client.return_value = Mock(
            session=Mock(
                post=Mock(
                    return_value=Mock(json=Mock(return_value={"token": "test_token"}))
                )
            )
        )
        xblock = make_an_xblock("instructor")
        student_view = xblock.student_view()
        mock_superset_client.assert_called_once()
        html = student_view.content
        self.assertIsNotNone(html)
        self.assertIn("superset-embedded-container", html)

    def test_render_student(self):
        """
        Ensure students see a warning message, not Superset.
        """
        xblock = make_an_xblock("student")
        student_view = xblock.student_view()
        html = student_view.content
        self.assertIsNotNone(html)
        self.assertNotIn("superset-embedded-container", html)
        self.assertIn("Superset is only visible to course staff and instructors", html)

    @patch("platform_plugin_aspects.xblock.pkg_resources.resource_exists")
    @patch("platform_plugin_aspects.xblock.translation.get_language")
    @patch("platform_plugin_aspects.utils._generate_guest_token")
    def test_render_translations(
        self, mock_generate_guest_token, mock_get_language, mock_resource_exists
    ):
        """
        Ensure translated javascript is served.
        """
        mock_generate_guest_token.return_value = ("test-token", "test-dashboard-uuid")
        mock_get_language.return_value = "eo"
        mock_resource_exists.return_value = True
        xblock = make_an_xblock("instructor")
        student_view = xblock.student_view()
        for resource in student_view.resources:
            if resource.kind == "url":
                url_resource = resource
        self.assertIsNotNone(url_resource, "No 'url' resource found in fragment")
        self.assertIn("eo/text.js", url_resource.data)

    @patch("platform_plugin_aspects.xblock.translation.get_language")
    @patch("platform_plugin_aspects.utils._generate_guest_token")
    def test_render_no_translations(
        self,
        mock_generate_guest_token,
        mock_get_language,
    ):
        """
        Ensure translated javascript is served.
        """
        mock_generate_guest_token.return_value = ("test-token", "test-dashboard-uuid")
        mock_get_language.return_value = None
        xblock = make_an_xblock("instructor")
        student_view = xblock.student_view()
        for resource in student_view.resources:
            assert resource.kind != "url"
