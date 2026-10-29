"""Pathway Enrollment sink"""

from platform_plugin_aspects.sinks.base_sink import ModelBaseSink
from platform_plugin_aspects.sinks.serializers import PathwayEnrollmentSerializer


class PathwayEnrollmentSink(ModelBaseSink):  # pylint: disable=abstract-method
    """
    Sink for the openedx-core PathwayEnrollment model
    """

    model = "pathway_enrollment"
    unique_key = "id"
    clickhouse_table_name = "pathway_enrollment"
    timestamp_field = "time_last_dumped"
    name = "Pathway Enrollment"
    serializer_class = PathwayEnrollmentSerializer

    def get_queryset(self, start_pk=None):
        return super().get_queryset(start_pk).select_related("user")
