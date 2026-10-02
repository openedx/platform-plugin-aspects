"""User profile sink"""

from platform_plugin_aspects.sinks.base_sink import ModelBaseSink
from platform_plugin_aspects.sinks.serializers import UserProfileSerializer


class UserProfileSink(ModelBaseSink):  # pylint: disable=abstract-method
    """
    Sink for user profile events
    """

    model = "user_profile"
    unique_key = "id"
    clickhouse_table_name = "user_profile"
    timestamp_field = "time_last_dumped"
    name = "User Profile"
    serializer_class = UserProfileSerializer

    def get_queryset(self, start_pk=None):
        return super().get_queryset(start_pk).select_related("user")
