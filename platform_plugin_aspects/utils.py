"""
Utilities for the Aspects app.
"""

from __future__ import annotations

import copy
import logging
import os
import uuid
from importlib import import_module
from urllib.parse import urljoin

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.urls import reverse
from requests.exceptions import HTTPError
from supersetapiclient.client import SupersetClient
from xblock.reference.user_service import XBlockUser

logger = logging.getLogger(__name__)

if settings.DEBUG:  # pragma: no cover
    os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"


def _(text):
    """
    Define a dummy `gettext` replacement to make string extraction tools scrape strings marked for translation.
    """
    return text


DEFAULT_FILTERS_FORMAT = [
    "org = '{course_id.org}'",
    "course_key = '{course_id}'",
]


def generate_superset_context(
    context,
    dashboards,
    language=None,
) -> dict:
    """
    Update context with superset token and dashboard id.

    Args:
        context (dict): the context for the instructor dashboard. It must include a course_id.
        user (XBlockUser or User): the current user.
        superset_config (dict): superset config.
        dashboards (list): list of superset dashboard uuid.
        filters (list): list of filters to apply to the dashboard.
        language (str): the language code of the end user.
    """
    course_id = context["course_id"]
    superset_config = settings.SUPERSET_CONFIG

    # We're modifying this, keep a local copy
    rtn_dashboards = copy.deepcopy(dashboards)

    if language:
        for dashboard in rtn_dashboards:
            if not dashboard.get("allow_translations"):
                continue
            dashboard["slug"] = f"{dashboard['slug']}-{language}"
            dashboard["uuid"] = get_localized_uuid(dashboard["uuid"], language)

    superset_url = _fix_service_url(superset_config.get("service_url"))

    # Use an absolute LMS URL here, just in case we're being rendered in an MFE.
    guest_token_url = urljoin(
        settings.LMS_ROOT_URL,
        reverse(
            "platform_plugin_aspects:superset_guest_token",
            kwargs={"course_id": course_id},
        ),
    )

    context.update(
        {
            "superset_dashboards": rtn_dashboards,
            "superset_url": superset_url,
            "superset_guest_token_url": guest_token_url,
        }
    )

    return context


def generate_guest_token(user, course, dashboards, filters) -> str:
    """
    Generate and return a Superset guest token for the user.

    Raise ImproperlyConfigured if the Superset API client request fails for any reason.

    Args:
        user: User object.
        course: Course object, used to populate `filters` template strings.
        dashboards: list of dashboard UUIDs to grant access to.
        filters: list of string filters to apply.

    Returns:
        tuple: Superset guest token and dashboard id.
        or None, exception if Superset is missconfigured or cannot generate guest token.
    """
    superset_config = settings.SUPERSET_CONFIG
    superset_internal_host = _fix_service_url(
        superset_config.get("internal_service_url")
        or superset_config.get("service_url")
    )
    superset_username = superset_config.get("username")
    superset_password = superset_config.get("password")

    formatted_filters = [
        filter.format(course_id=course, user=user) for filter in filters
    ]

    resources = []

    # Get permissions for all localized versions of the dashboards
    for dashboard in dashboards:
        resources.append({"type": "dashboard", "id": dashboard["uuid"]})

        if dashboard.get("allow_translations"):
            for locale in settings.SUPERSET_DASHBOARD_LOCALES:
                resources.append(
                    {
                        "type": "dashboard",
                        "id": get_localized_uuid(dashboard["uuid"], locale),
                    }
                )

    data = {
        "user": _superset_user_data(user),
        "resources": resources,
        "rls": [{"clause": filter} for filter in formatted_filters],
    }

    try:
        client = SupersetClient(
            host=superset_internal_host,
            username=superset_username,
            password=superset_password,
        )
        response = client.session.post(
            url=f"{superset_internal_host}api/v1/security/guest_token/",
            json=data,
            headers={"Content-Type": "application/json"},
        )
        response.raise_for_status()
        token = response.json().get("token")
        return token

    except HTTPError as err:
        # Superset server errors sometimes come with messages, so log the response.
        logger.error(
            f"{err.response.status_code} {err.response.json()} for url: {err.response.url}, data: {data}"
        )
        raise ImproperlyConfigured(
            _(
                "Unable to fetch Superset guest token, "
                "Superset server error {server_response}"
            ).format(server_response=err.response.json())
        ) from err

    except Exception as exc:
        logger.error(exc)
        raise ImproperlyConfigured(
            _(
                "Unable to fetch Superset guest token, "
                "mostly likely due to invalid settings.SUPERSET_CONFIG"
            )
        ) from exc


def _fix_service_url(url: str) -> str:
    """
    Append a trailing slash to the given url, if missing.

    SupersetClient requires a trailing slash for service URLs.
    """
    if url and url[-1] != "/":
        url += "/"
    return url


def _superset_user_data(user: XBlockUser) -> dict:
    """
    Return the user properties sent to the Superset API.
    """
    # We can send more info about the user to superset
    # but Open edX only provides the full name. For now is not needed
    # and doesn't add any value so we don't send it.
    # {
    #    "first_name": "John",
    #    "last_name": "Doe",
    # }
    username = None
    # Django User
    if hasattr(user, "username"):
        username = user.username
    else:
        assert isinstance(user, XBlockUser)
        username = user.opt_attrs.get("edx-platform.username")

    return {
        "username": username,
    }


def get_model(model_setting):
    """Load a model from a setting."""
    MODEL_CONFIG = getattr(settings, "EVENT_SINK_CLICKHOUSE_MODEL_CONFIG", {})

    model_config = MODEL_CONFIG.get(model_setting)
    if not model_config:
        logger.error("Unable to find model config for %s", model_setting)
        return None

    module = model_config.get("module")
    if not module:
        logger.error("Module was not specified in %s", model_setting)
        return None

    model_name = model_config.get("model")
    if not model_name:
        logger.error("Model was not specified in %s", model_setting)
        return None

    try:
        model = getattr(import_module(module), model_name)
        return model
    except (ImportError, AttributeError, ModuleNotFoundError):
        logger.error("Unable to load model %s.%s", module, model_name)

    return None


def get_modulestore():  # pragma: no cover
    """
    Import and return modulestore.

    Placed here to avoid model import at startup and to facilitate mocking them in testing.
    """
    # pylint: disable=import-outside-toplevel,import-error
    from xmodule.modulestore.django import modulestore

    return modulestore()


def get_detached_xblock_types():  # pragma: no cover
    """
    Import and return DETACHED_XBLOCK_TYPES.

    Placed here to avoid model import at startup and to facilitate mocking them in testing.
    """
    # pylint: disable=import-outside-toplevel,import-error
    from xmodule.modulestore.store_utilities import DETACHED_XBLOCK_TYPES

    return DETACHED_XBLOCK_TYPES


def get_ccx_courses(course_id):
    """
    Get the CCX courses for a given course.
    """
    if settings.FEATURES.get("CUSTOM_COURSES_EDX"):
        return get_model("custom_course_edx").objects.filter(course_id=course_id)
    return []


def get_localized_uuid(base_uuid, language):
    """
    Generate an idempotent uuid.
    """
    base_uuid = uuid.UUID(base_uuid)
    base_namespace = uuid.uuid5(base_uuid, "superset")
    normalized_language = language.lower().replace("-", "_")
    return str(uuid.uuid5(base_namespace, normalized_language))


def _get_object_tags(usage_key):  # pragma: no cover
    """
    Wrap the Open edX tagging API method get_object_tags.
    """
    try:
        # pylint: disable=import-outside-toplevel
        from openedx.core.djangoapps.content_tagging.api import get_object_tags

        return get_object_tags(object_id=str(usage_key))
    # Pre-Redwood versions of Open edX don't have this API
    except ImportError:
        return {}


def get_tags_for_block(usage_key) -> set:
    """
    Return all the tags (and their parent tags) applied to the given block.

    Returns a set of tag id: [1, 2, 3]
    """
    object_tags = _get_object_tags(usage_key)
    serialized_tags = set()
    for object_tag in object_tags:
        tag = object_tag.tag
        while tag:
            serialized_tags.add(tag.id)
            tag = tag.parent

    return list(serialized_tags)
