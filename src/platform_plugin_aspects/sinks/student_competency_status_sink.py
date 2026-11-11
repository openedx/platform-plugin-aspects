"""Student Competency Status sinks: per competency and per criteria group"""

from platform_plugin_aspects.sinks.base_sink import ModelBaseSink
from platform_plugin_aspects.sinks.serializers import (
    StudentCompetencyCriteriaGroupStatusSerializer,
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


class StudentCompetencyCriteriaGroupStatusSink(ModelBaseSink):  # pylint: disable=abstract-method
    """
    Sink for the openedx-core StudentCompetencyCriteriaGroupStatus model: a learner's current
    mastery status for one criteria group, which is the only place AttemptedNotDemonstrated is
    stored and, for course-level groups, the learner's status in one course
    """

    model = "student_competency_criteria_group_status"
    unique_key = "id"
    clickhouse_table_name = "student_competency_criteria_group_status"
    timestamp_field = "time_last_dumped"
    name = "Student Competency Criteria Group Status"
    serializer_class = StudentCompetencyCriteriaGroupStatusSerializer

    def get_queryset(self, start_pk=None):
        return (
            super()
            .get_queryset(start_pk)
            .select_related("user", "status", "group__tag", "group__course")
        )
