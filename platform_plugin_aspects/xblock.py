"""XBlock to embed Superset dashboards in Open edX."""

from __future__ import annotations

import json
import logging

import pkg_resources
from django.core.exceptions import ImproperlyConfigured
from django.utils import translation
from web_fragments.fragment import Fragment
from webob import Response
from xblock.core import XBlock
from xblock.exceptions import JsonHandlerError
from xblock.fields import List, Scope, String

# These moved from xblockutils to xblock in Quince, these can be removed
# when we stop supporting earlier versions.
try:  # pragma: no cover
    from xblock.utils.resources import ResourceLoader
    from xblock.utils.studio_editable import StudioEditableXBlockMixin
except ImportError:  # pragma: no cover
    from xblockutils.resources import ResourceLoader
    from xblockutils.studio_editable import StudioEditableXBlockMixin

from .utils import (
    DEFAULT_FILTERS_FORMAT,
    _,
    generate_guest_token,
    generate_superset_context,
)

log = logging.getLogger(__name__)
loader = ResourceLoader(__name__)


@XBlock.needs("user")
@XBlock.needs("i18n")
class SupersetXBlock(StudioEditableXBlockMixin, XBlock):
    """
    XBlock provides a way to embed dashboards from Superset in a course.
    """

    editable_fields = ("display_name", "dashboard_uuid", "filters")

    display_name = String(
        display_name=_("Display name"),
        help=_("Display name"),
        default=_("Superset Dashboard"),
        scope=Scope.settings,
    )

    dashboard_uuid = String(
        display_name=_("Dashboard UUID"),
        help=_(
            "The ID of the dashboard to embed. Available in the Superset embed dashboard UI."
        ),
        default="",
        scope=Scope.settings,
    )

    filters = List(
        display_name=_("Filters"),
        help=_(
            """List of SQL filters to apply to the
               dashboard. E.g: ["org='edX'", "country in ('us', 'co')"]
               The fields used here must be available on every dataset used by the dashboard.
               """
        ),
        default=[],
        scope=Scope.settings,
    )

    def dashboards(self):
        """
        Return an array of dashboards configured for this XBlock.
        """
        if self.dashboard_uuid:
            return [{"name": self.display_name, "uuid": self.dashboard_uuid}]
        else:
            return []

    def render_template(self, template_path, context=None) -> str:
        """
        Render a template with the given context.

        The template is translatedaccording to the user's language.

        args:
            template_path: The path to the template
            context: The context to render in the template

        returns:
            The rendered template
        """
        return loader.render_django_template(
            template_path, context, i18n_service=self.runtime.service(self, "i18n")
        )

    def user_is_student(self, user) -> bool:
        """
        Check if the user is a student.
        """
        return not user or user.opt_attrs.get("edx-platform.user_role") == "student"

    def student_view(self, context=None):
        """
        Render the view shown to users of this XBlock.
        """
        user_service = self.runtime.service(self, "user")
        user = user_service.get_current_user()

        context = context or {}
        context.update(
            {
                "course_id": self.runtime.course_id,
                "display_name": self.display_name,
            }
        )

        # Hide Superset content from non-course staff.
        if self.user_is_student(user):
            frag = Fragment()
            frag.add_content(
                self.render_template("static/html/superset_student.html", context)
            )
            return frag

        context = generate_superset_context(
            context=context,
            dashboards=self.dashboards(),
        )
        context["xblock_id"] = str(self.scope_ids.usage_id.block_id)

        # Remove this URL from the context to avoid confusion.
        # Our XBlock handler URL will be used instead, provided in superset.js
        del context["superset_guest_token_url"]

        frag = Fragment()
        frag.add_content(self.render_template("static/html/superset.html", context))
        frag.add_css(loader.load_unicode("static/css/superset.css"))
        frag.add_javascript(loader.load_unicode("static/js/install_required.js"))

        # Add i18n js
        statici18n_js_url = self._get_statici18n_js_url()
        if statici18n_js_url:
            frag.add_javascript_url(
                self.runtime.local_resource_url(self, statici18n_js_url)
            )
        frag.add_javascript(loader.load_unicode("static/js/embed_dashboard.js"))
        frag.add_javascript(loader.load_unicode("static/js/superset.js"))
        frag.initialize_js(
            "SupersetXBlock",
            json_args={
                "dashboard_uuid": self.dashboard_uuid,
                "superset_url": context.get("superset_url"),
                "xblock_id": context.get("xblock_id"),
            },
        )
        return frag

    @staticmethod
    def workbench_scenarios():  # pragma: no cover
        """Return a canned scenario for display in the workbench."""
        return [
            (
                "SupersetXBlock",
                """<superset/>
             """,
            ),
            (
                "Multiple SupersetXBlock",
                """<vertical_demo>
                <superset/>
                <superset/>
                <superset/>
                </vertical_demo>
             """,
            ),
        ]

    @staticmethod
    def _get_statici18n_js_url():
        """
        Return the Javascript translation file for the currently selected language, if any.

        Defaults to English if available.
        """
        locale_code = translation.get_language()
        if locale_code is None:
            return None
        text_js = "public/js/translations/{locale_code}/text.js"
        lang_code = locale_code.split("-")[0]
        for code in (locale_code, lang_code, "en"):
            if pkg_resources.resource_exists(
                loader.module_name, text_js.format(locale_code=code)
            ):
                return text_js.format(locale_code=code)
        return None

    @XBlock.json_handler
    def get_superset_guest_token(
        self, request_body, suffix=""
    ):  # pylint: disable=unused-argument
        """Return a guest token for Superset."""
        user_service = self.runtime.service(self, "user")
        user = user_service.get_current_user()

        try:
            guest_token = generate_guest_token(
                user=user,
                course=self.scope_ids.usage_id.context_key,
                dashboards=self.dashboards(),
                filters=DEFAULT_FILTERS_FORMAT + self.filters,
            )
        except ImproperlyConfigured as exc:
            raise JsonHandlerError(500, str(exc)) from exc

        return Response(
            json.dumps({"guestToken": guest_token}),
            content_type="application/json",
            charset="UTF-8",
        )
