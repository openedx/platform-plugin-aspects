"""
This file contains a management command for exporting course modulestore data to ClickHouse.
"""

import logging
from importlib import import_module

from celery import shared_task
from edx_django_utils.monitoring import set_code_owner_attribute
from opaque_keys.edx.keys import CourseKey

from platform_plugin_aspects.sinks import CourseOverviewSink
from platform_plugin_aspects.utils import get_ccx_courses

log = logging.getLogger(__name__)
celery_log = logging.getLogger("edx.celery.task")


@shared_task
@set_code_owner_attribute
def dump_course_to_clickhouse(course_key_string, connection_overrides=None):
    """
    Serialize a course and writes it to ClickHouse.

    Arguments:
        course_key_string: course key for the course to be exported
        connection_overrides (dict):  overrides to ClickHouse connection
            parameters specified in `settings.EVENT_SINK_CLICKHOUSE_BACKEND_CONFIG`.
    """
    if CourseOverviewSink.is_enabled():  # pragma: no cover
        course_key = CourseKey.from_string(course_key_string)
        sink = CourseOverviewSink(
            connection_overrides=connection_overrides, log=celery_log
        )
        sink.dump(course_key)

        ccx_courses = get_ccx_courses(course_key)
        for ccx_course in ccx_courses:
            ccx_course_key = str(ccx_course.locator)
            sink.dump(ccx_course_key)


@shared_task
@set_code_owner_attribute
def dump_data_to_clickhouse(
    sink_module, sink_name, object_id, connection_overrides=None
):
    """
    Serialize a data and writes it to ClickHouse.

    Arguments:
        sink_module: module path of sink
        sink_name: name of sink class
        object_id: id of object
        connection_overrides (dict):  overrides to ClickHouse connection
    """
    Sink = getattr(import_module(sink_module), sink_name)

    if Sink.is_enabled():
        sink = Sink(connection_overrides=connection_overrides, log=celery_log)
        sink.dump(object_id)
        return "Dumped"

    return "Disabled"
