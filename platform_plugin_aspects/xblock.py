"""XBlock to embed a Superset dashboards in Open edX."""
from __future__ import annotations

import logging
from typing import Tuple

import pkg_resources
from django.conf import settings
from django.utils import translation
from web_fragments.fragment import Fragment
from xblock.core import XBlock
from xblock.fields import List, Scope, String
from xblockutils.resources import ResourceLoader

from .utils import _, update_context

log = logging.getLogger(__name__)
loader = ResourceLoader(__name__)


@XBlock.wants("user")
@XBlock.needs("i18n")
class SupersetXBlock(XBlock):
    """
    Superset XBlock provides a way to embed dashboards from Superset in a course.
    """

    display_name = String(
        display_name=_("Display name"),
        help=_("Display name"),
        default="Superset Dashboard",
        scope=Scope.settings,
    )

    superset_url = String(
        display_name=_("Superset URL"),
        help=_("Superset URL to embed the dashboard."),
        default="",
        scope=Scope.settings,
    )

    superset_username = String(
        display_name=_("Superset Username"),
        help=_("Superset Username"),
        default="",
        scope=Scope.settings,
    )

    superset_password = String(
        display_name=_("Superset Password"),
        help=_("Superset Password"),
        default="",
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
            """Semicolon separated list of SQL filters to apply to the
               dashboard. E.g: org='edX'; country in ('us', 'co').
               The fields used here must be available on every dataset used by the dashboard.
               """
        ),
        default=[],
        scope=Scope.settings,
    )

    def resource_string(self, path):
        """Handy helper for getting resources from our kit."""
        data = pkg_resources.resource_string(__name__, path)
        return data.decode("utf8")

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

    def user_is_staff(self, user) -> bool:
        """
        Check whether the user has course staff permissions for this XBlock.
        """
        return user.opt_attrs.get("edx-platform.user_is_staff")

    def is_student(self, user) -> bool:
        """
        Check if the user is a student.
        """
        return user.opt_attrs.get("edx-platform.user_role") == "student"

    def anonymous_user_id(self, user) -> str:
        """
        Return the anonymous user ID of the user.
        """
        return user.opt_attrs.get("edx-platform.anonymous_user_id")

    def student_view(self, context=None):
        """
        Render the view shown to students.
        """
        user_service = self.runtime.service(self, "user")
        user = user_service.get_current_user()

        context.update(
            {
                "self": self,
                "user": user,
                "course": self.course_id,
                "display_name": self.display_name,
            }
        )

        superset_config = getattr(settings, "SUPERSET_CONFIG", {})

        xblock_superset_config = {
            "username": self.superset_username or superset_config.get("username"),
            "password": self.superset_password or superset_config.get("password"),
        }

        if self.superset_url:
            xblock_superset_config["service_url"] = self.superset_url

        if self.dashboard_uuid:
            context = update_context(
                context=context,
                superset_config=xblock_superset_config,
                dashboard_uuid=self.dashboard_uuid,
                filters=self.filters,
            )

            context["xblock_id"] = self.scope_ids.usage_id.block_id

        frag = Fragment()
        frag.add_content(self.render_template("static/html/superset.html", context))
        frag.add_css(self.resource_string("static/css/superset.css"))
        frag.add_javascript(self.resource_string("static/js/install_required.js"))

        # Add i18n js
        statici18n_js_url = self._get_statici18n_js_url()
        if statici18n_js_url:
            frag.add_javascript_url(
                self.runtime.local_resource_url(self, statici18n_js_url)
            )
        frag.add_javascript(self.resource_string("static/js/embed_dashboard.js"))
        frag.add_javascript(self.resource_string("static/js/superset.js"))
        frag.initialize_js(
            "SupersetXBlock",
            json_args={
                "superset_url": self.superset_url or superset_config.get("host"),
                "superset_username": self.superset_username,
                "superset_password": self.superset_password,
                "dashboard_uuid": self.dashboard_uuid,
                "superset_token": context.get("superset_token"),
                "xblock_id": self.scope_ids.usage_id.block_id,
            },
        )
        return frag

    def studio_view(self, context=None):
        """
        Render the view shown to course authors.
        """
        filters = "; ".join(self.filters)
        context = {
            "display_name": self.display_name,
            "superset_url": self.superset_url,
            "superset_username": self.superset_username,
            "superset_password": self.superset_password,
            "dashboard_uuid": self.dashboard_uuid,
            "filters": filters,
            "display_name_field": self.fields[  # pylint: disable=unsubscriptable-object
                "display_name"
            ],
            "superset_url_field": self.fields[  # pylint: disable=unsubscriptable-object
                "superset_url"
            ],
            "superset_username_field": self.fields[  # pylint: disable=unsubscriptable-object
                "superset_username"
            ],
            "superset_password_field": self.fields[  # pylint: disable=unsubscriptable-object
                "superset_password"
            ],
            "dashboard_uuid_field": self.fields[  # pylint: disable=unsubscriptable-object
                "dashboard_uuid"
            ],
            "filters_field": self.fields[  # pylint: disable=unsubscriptable-object
                "filters"
            ],
        }

        frag = Fragment()
        frag.add_content(
            self.render_template("static/html/superset_edit.html", context)
        )
        frag.add_css(self.resource_string("static/css/superset.css"))

        # Add i18n js
        statici18n_js_url = self._get_statici18n_js_url()
        if statici18n_js_url:
            frag.add_javascript_url(
                self.runtime.local_resource_url(self, statici18n_js_url)
            )

        frag.add_javascript(self.resource_string("static/js/superset_edit.js"))
        frag.initialize_js("SupersetXBlock")
        return frag

    @XBlock.json_handler
    def studio_submit(self, data, suffix=""):  # pylint: disable=unused-argument
        """
        Save studio updates.
        """
        self.display_name = data.get("display_name")
        self.superset_url = data.get("superset_url")
        self.superset_username = data.get("superset_username")
        self.superset_password = data.get("superset_password")
        self.dashboard_uuid = data.get("dashboard_uuid")
        filters = data.get("filters")
        self.filters = []
        if filters:
            for rlsf in filters.split(";"):
                rlsf = rlsf.strip()
                self.filters.append(rlsf)

    @staticmethod
    def get_fullname(user) -> Tuple[str, str]:
        """
        Return the full name of the user.

        args:
            user: The user to get the fullname

        returns:
            A tuple containing the first name and last name of the user
        """
        first_name, last_name = "", ""

        if user.full_name:
            fullname = user.full_name.split(" ", 1)
            first_name = fullname[0]

            if fullname[1:]:
                last_name = fullname[1]

        return first_name, last_name

    @staticmethod
    def workbench_scenarios():
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

    @staticmethod
    def get_dummy():
        """
        Return dummy method to generate initial i18n.
        """
        return translation.gettext_noop("Dummy")
