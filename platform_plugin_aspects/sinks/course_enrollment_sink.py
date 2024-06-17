"""User profile sink"""

from platform_plugin_aspects.sinks.base_sink import ModelBaseSink
from platform_plugin_aspects.sinks.serializers import CourseEnrollmentSerializer


class CourseEnrollmentSink(ModelBaseSink):  # pylint: disable=abstract-method
    """
    Sink for user CourseEnrollment model
    """

    model = "course_enrollment"
    unique_key = "id"
    clickhouse_table_name = "course_enrollment"
    timestamp_field = "time_last_dumped"
    name = "Course Enrollment"
    serializer_class = CourseEnrollmentSerializer

    def get_queryset(self, start_pk=None):
        return super().get_queryset(start_pk).select_related("user")
