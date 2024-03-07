"""
Open edX Filters needed for Aspects integration.
"""

import pkg_resources
from crum import get_current_user
from django.conf import settings
from django.template import Context, Template
from openedx_filters import PipelineStep
from web_fragments.fragment import Fragment

from platform_plugin_aspects.utils import generate_superset_context

TEMPLATE_ABSOLUTE_PATH = "/instructor_dashboard/"
BLOCK_CATEGORY = "aspects"

ASPECTS_SECURITY_FILTERS_FORMAT = [
    "org = '{course.org}'",
    "course_name = '{course.display_name}'",
    "course_run = '{course.id.run}'",
]


class AddSupersetTab(PipelineStep):
    """
    Add superset tab to instructor dashboard.

    Enable in the LMS by adding this stanza to OPEN_EDX_FILTERS_CONFIG:

      "org.openedx.learning.instructor.dashboard.render.started.v1": {
        "fail_silently": False,
        "pipeline": [
          "platform_plugin_aspects.extensions.filters.AddSupersetTab",
        ]
      }
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
        dashboard_uuid = settings.ASPECTS_INSTRUCTOR_DASHBOARD_UUID
        extra_filters_format = settings.SUPERSET_EXTRA_FILTERS_FORMAT

        filters = ASPECTS_SECURITY_FILTERS_FORMAT + extra_filters_format

        user = get_current_user()

        context = generate_superset_context(
            context,
            user,
            dashboard_uuid=dashboard_uuid,
            filters=filters,
        )

        template = Template(self.resource_string("static/html/superset.html"))
        html = template.render(Context(context))
        frag = Fragment(html)
        frag.add_css(self.resource_string("static/css/superset.css"))
        frag.add_javascript(self.resource_string("static/js/embed_dashboard.js"))
        section_data = {
            "fragment": frag,
            "section_key": BLOCK_CATEGORY,
            "section_display_name": BLOCK_CATEGORY.title(),
            "course_id": str(course.id),
            "template_path_prefix": TEMPLATE_ABSOLUTE_PATH,
        }
        context["sections"].append(section_data)
        return {
            "context": context,
        }

    def resource_string(self, path):
        """Handy helper for getting resources from our kit."""
        data = pkg_resources.resource_string("platform_plugin_aspects", path)
        return data.decode("utf8")
