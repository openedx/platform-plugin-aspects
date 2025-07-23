#!/usr/bin/env python
"""
Test basic SupersetXBlock display function
"""

import json
from unittest import TestCase
from unittest.mock import Mock, patch

from django.core.exceptions import ImproperlyConfigured
from opaque_keys.edx.locator import CourseLocator
from webob import Request
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

    def handler_url(_self, handler, *args, **kwargs):
        """
        Mock runtime.handlerUrl

        The LMS and CMS runtimes implement handlerUrl, but we have to mock it here.
        """
        return f"/{handler}"

    runtime = Mock(
        course_id=course_id,
        service=service,
        local_resource_url=Mock(side_effect=local_resource_url),
        handlerUrl=Mock(side_effect=handler_url),
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

    def test_render_instructor(self):
        """
        Ensure staff can see the Superset dashboard.
        """
        xblock = make_an_xblock("instructor")
        student_view = xblock.student_view()
        html = student_view.content
        self.assertIsNotNone(html)
        self.assertIn(
            "Dashboard UUID is not set. Please set the dashboard UUID in the Studio.",
            html,
        )

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

    @patch("platform_plugin_aspects.xblock.translation.get_language")
    def test_render_translations(self, mock_get_language):
        """
        Ensure translated javascript is served.
        """
        mock_get_language.return_value = "eo"
        xblock = make_an_xblock("instructor")
        student_view = xblock.student_view()
        url_resource = None
        for resource in student_view.resources:
            if resource.kind == "url":
                url_resource = resource
                self.assertIsNotNone(
                    url_resource, "No 'url' resource found in fragment"
                )
                self.assertIn("eo/text.js", url_resource.data)
        mock_get_language.assert_called_once()

    @patch("platform_plugin_aspects.xblock.translation.get_language")
    def test_render_no_translations(
        self,
        mock_get_language,
    ):
        """
        Ensure translated javascript is served.
        """
        mock_get_language.return_value = None
        xblock = make_an_xblock("instructor")
        student_view = xblock.student_view()
        for resource in student_view.resources:
            assert resource.kind != "url"
        mock_get_language.assert_called_once()

    @patch("platform_plugin_aspects.utils.SupersetClient")
    def test_guest_token_handler(self, mock_superset_client):
        response_mock = Mock(status_code=200)
        mock_superset_client.return_value.session.post.return_value = response_mock
        response_mock.json.return_value = {
            "token": "test-token",
        }

        request = Request.blank("/")
        request.method = "POST"
        request.body = b"{}"
        xblock = make_an_xblock("instructor")
        xblock.dashboard_uuid = "1d6bf904-f53f-47fd-b1c9-6cd7e284d286"
        response = xblock.get_superset_guest_token(request)

        assert response.status_code == 200
        data = json.loads(response.body.decode("utf-8"))
        assert data.get("guestToken") == "test-token"
        mock_superset_client.assert_called_once()

    @patch("platform_plugin_aspects.views.generate_guest_token")
    def test_guest_token_handler_failed(self, mock_generate_guest_token):
        mock_generate_guest_token.side_effect = ImproperlyConfigured

        request = Request.blank("/")
        request.method = "POST"
        request.body = b"{}"
        xblock = make_an_xblock("instructor")
        response = xblock.get_superset_guest_token(request)

        assert response.status_code == 500
        data = json.loads(response.body.decode("utf-8"))
        assert (
            "Unable to fetch Superset guest token, mostly likely due to invalid "
            "settings.SUPERSET_CONFIG or because one of the dashboard UUIDs requested"
            in data.get("error")
        )
