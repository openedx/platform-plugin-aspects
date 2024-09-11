# pyright: reportMissingImports=false

"""Xblock aside enabling OpenAI driven summaries."""

import logging

import pkg_resources
from django.template import Context, Template
from django.utils import translation
from web_fragments.fragment import Fragment
from common.djangoapps.edxmako.shortcuts import render_to_string
from xblock.core import XBlock, XBlockAside
from xblock.fields import Scope, String
from xblock.utils.resources import ResourceLoader

logger = logging.getLogger(__name__)
loader = ResourceLoader(__name__)

from platform_plugin_aspects.xblock import ResourceLoader

@XBlock.needs("user")
@XBlock.needs("i18n")
class AspectsAside(XBlockAside):
    """
    XBlock aside that injects a superset dashboard for instructors.
    """

    def _get_block(self):
        """
        Get the block wrapped by this aside.
        """
        from xmodule.modulestore.django import modulestore  # pylint: disable=import-error, import-outside-toplevel

        return modulestore().get_item(self.scope_ids.usage_id.usage_key)

    @XBlockAside.aside_for("studio_view")
    @XBlockAside.aside_for("author_view")
    @XBlockAside.aside_for("student_view")
    def student_view_aside(self, block, context):  # pylint: disable=unused-argument
        """
        Display the tag selector with specific categories and allowed values,
        depending on the context.
        """
        logger.info(f"Class name {block.__class__.__name__}")
        if block.__class__.__name__.replace("WithMixins", "") in ['ProblemBlock']:
            frag = Fragment()
            context.update({
                "xblock_id": self.scope_ids.usage_id.usage_key
            })
            frag.add_content(self.render_template("static/html/example.html", context))
            # frag.add_javascript_url(self._get_studio_resource_url('/js/xblock_asides/structured_tags.js'))
            # frag.initialize_js('StructuredTagsInit')
            return frag
        return Fragment()

    @classmethod
    def should_apply_to_block(cls, block):
        """
        Override base XBlockAside implementation.

        Indicates whether this aside should apply to a given block type, course, and user.
        """
        # logger.info(block.__dict__)
        return True


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