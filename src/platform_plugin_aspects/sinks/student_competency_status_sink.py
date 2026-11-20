"""Student Competency Status sinks: per competency, and per competency and course"""

from platform_plugin_aspects.sinks.base_sink import ModelBaseSink
from platform_plugin_aspects.sinks.serializers import (
    StudentCompetencyCourseStatusSerializer,
    StudentCompetencyStatusSerializer,
)


class StudentCompetencyStatusSink(ModelBaseSink):  # pylint: disable=abstract-method
    """
    Sink for the openedx-core StudentCompetencyStatus model: a learner's current mastery status for one competency
    """

    model = "student_competency_status"
    unique_key = "id"
    clickhouse_table_name = "student_competency_status"
    timestamp_field = "time_last_dumped"
    name = "Student Competency Status"
    serializer_class = StudentCompetencyStatusSerializer

    def get_queryset(self, start_pk=None):
        return super().get_queryset(start_pk).select_related("user", "tag", "status")

    def get_object(self, item_id):
        return self.get_queryset().get(id=item_id)


class StudentCompetencyCourseStatusSink(
    ModelBaseSink
):  # pylint: disable=abstract-method
    """
    Sink for openedx-core StudentCompetencyCriteriaGroupStatus rows of course-level groups.

    A course-level group (one with a course run) holds the learner's status for one competency
    in one course, the only place AttemptedNotDemonstrated is stored per competency and course.
    Root and leaf group rows are not sunk: nothing in Aspects reads them, and they would
    multiply the rows.
    """

    model = "student_competency_course_status"
    unique_key = "id"
    clickhouse_table_name = "student_competency_course_status"
    timestamp_field = "time_last_dumped"
    name = "Student Competency Course Status"
    serializer_class = StudentCompetencyCourseStatusSerializer

    @staticmethod
    def is_course_level(status):
        """Return True if ``status`` belongs to a course-level group, the only rows this sink dumps."""
        return status.group.course_id is not None

    def get_queryset(self, start_pk=None):
        return (
            super()
            .get_queryset(start_pk)
            .filter(group__course__isnull=False)
            .select_related("user", "status", "group__tag", "group__course")
        )

    def get_object(self, item_id):
        return self.get_queryset().get(id=item_id)
