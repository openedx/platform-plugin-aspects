"""
Open edX Filters needed for Aspects integration.
"""

import pkg_resources
from crum import get_current_user
from django.conf import settings
from django.template import Context, Template
from openedx_filters import PipelineStep
from web_fragments.fragment import Fragment

from platform_plugin_aspects.utils import _, generate_superset_context, get_model

TEMPLATE_ABSOLUTE_PATH = "/instructor_dashboard/"
BLOCK_CATEGORY = "aspects"


class AddSupersetTab(PipelineStep):
    """
    Add superset tab to instructor dashboard.
    """

    def run_filter(
        self, context, template_name
    ):  # pylint: disable=arguments-differ, unused-argument
        """Execute filter that modifies the instructor dashboard context.
        Args:
            context (dict): the context for the instructor dashboard.
            _ (str): instructor dashboard template name.
        """
        course = context["course"]
        dashboards = settings.ASPECTS_INSTRUCTOR_DASHBOARDS
        show_dashboard_link = settings.SUPERSET_SHOW_INSTRUCTOR_DASHBOARD_LINK

        user = get_current_user()

        try:
            user_language = (
                get_model("user_preference").get_value(user, "pref-lang") or "en"
            )
        # If there is no user_preferences model defined this will get thrown
        except AttributeError:
            user_language = "en"

        formatted_language = user_language.lower().replace("-", "_")
        if formatted_language not in [
            loc.lower().replace("-", "_") for loc in settings.SUPERSET_DASHBOARD_LOCALES
        ]:
            formatted_language = "en"

        context["course_id"] = course.id
        context = generate_superset_context(
            context,
            dashboards=dashboards,
            language=formatted_language,
        )

        template = Template(self.resource_string("static/html/superset.html"))
        html = template.render(Context(context))
        frag = Fragment(html)
        frag.add_css(self.resource_string("static/css/superset.css"))
        frag.add_javascript(self.resource_string("static/js/embed_dashboard.js"))
        section_data = {
            "fragment": frag,
            "section_key": BLOCK_CATEGORY,
            "section_display_name": _("Reports"),
            "course_id": str(context.get("course_id")),
            "superset_guest_token_url": str(context.get("superset_guest_token_url")),
            "superset_url": str(context.get("superset_url")),
            "template_path_prefix": TEMPLATE_ABSOLUTE_PATH,
            "show_dashboard_link": show_dashboard_link,
        }

        context["sections"].append(section_data)
        return {
            "context": context,
        }

    def resource_string(self, path):
        """Handy helper for getting resources from our kit."""
        data = pkg_resources.resource_string("platform_plugin_aspects", path)
        return data.decode("utf8")
