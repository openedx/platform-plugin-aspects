"""
Utilities for the Aspects app.
"""

from __future__ import annotations

import logging
import os
from importlib import import_module

from django.conf import settings
from supersetapiclient.client import SupersetClient
from xblock.reference.user_service import XBlockUser

logger = logging.getLogger(__name__)

if settings.DEBUG:
    os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"


def _(text):
    """
    Define a dummy `gettext` replacement to make string extraction tools scrape strings marked for translation.
    """
    return text


def generate_superset_context(  # pylint: disable=dangerous-default-value
    context,
    user,
    dashboards,
    filters=[],
):
    """
    Update context with superset token and dashboard id.

    Args:
        context (dict): the context for the instructor dashboard. It must include a course object
        user (XBlockUser or User): the current user.
        superset_config (dict): superset config.
        dashboards (list): list of superset dashboard uuid.
        filters (list): list of filters to apply to the dashboard.
    """
    course = context["course"]
    superset_config = settings.SUPERSET_CONFIG

    superset_token, dashboards = _generate_guest_token(
        user=user,
        course=course,
        superset_config=superset_config,
        dashboards=dashboards,
        filters=filters,
    )

    if superset_token:
        superset_url = _fix_service_url(superset_config.get("service_url"))
        context.update(
            {
                "superset_token": superset_token,
                "superset_dashboards": dashboards,
                "superset_url": superset_url,
            }
        )
    else:
        context.update(
            {
                "exception": str(dashboards),
            }
        )

    return context


def _generate_guest_token(user, course, superset_config, dashboards, filters):
    """
    Generate a Superset guest token for the user.

    Args:
        user: User object.
        course: Course object.

    Returns:
        tuple: Superset guest token and dashboard id.
        or None, exception if Superset is missconfigured or cannot generate guest token.
    """
    superset_internal_host = _fix_service_url(
        superset_config.get("internal_service_url")
        or superset_config.get("service_url")
    )
    superset_username = superset_config.get("username")
    superset_password = superset_config.get("password")

    try:
        client = SupersetClient(
            host=superset_internal_host,
            username=superset_username,
            password=superset_password,
        )
    except Exception as exc:  # pylint: disable=broad-except
        logger.error(exc)
        return None, exc

    formatted_filters = [filter.format(course=course, user=user) for filter in filters]

    data = {
        "user": _superset_user_data(user),
        "resources": [
            {"type": "dashboard", "id": dashboard["uuid"]} for dashboard in dashboards
        ],
        "rls": [{"clause": filter} for filter in formatted_filters],
    }

    try:
        logger.info(f"Requesting guest token from Superset, {data}")
        response = client.session.post(
            url=f"{superset_internal_host}api/v1/security/guest_token/",
            json=data,
            headers={"Content-Type": "application/json"},
        )
        response.raise_for_status()
        token = response.json()["token"]

        return token, dashboards
    except Exception as exc:  # pylint: disable=broad-except
        logger.error(exc)
        return None, exc


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
