"""User profile sink"""

from platform_plugin_aspects.sinks.base_sink import ModelBaseSink
from platform_plugin_aspects.sinks.serializers import UserExternalIDSerializer


class ExternalIdSink(ModelBaseSink):  # pylint: disable=abstract-method
    """
    Sink for user external ID serializer
    """

    model = "external_id"
    unique_key = "id"
    clickhouse_table_name = "external_id"
    timestamp_field = "time_last_dumped"
    name = "External ID"
    serializer_class = UserExternalIDSerializer

    def get_queryset(self, start_pk=None):
        return super().get_queryset(start_pk).select_related("user", "external_id_type")
