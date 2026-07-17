"""User retirement sink"""

import requests
from django.conf import settings

from platform_plugin_aspects.sinks.base_sink import ModelBaseSink
from platform_plugin_aspects.sinks.serializers import UserRetirementSerializer


class UserRetirementSink(ModelBaseSink):  # pylint: disable=abstract-method
    """
    Sink for user retirement events
    """

    model = "auth_user"
    unique_key = "id"
    clickhouse_table_name = (
        "dummy"  # uses settings.EVENT_SINK_CLICKHOUSE_PII_MODELS instead
    )
    timestamp_field = "modified"
    name = "User Retirement"
    serializer_class = UserRetirementSerializer

    def send_item(self, serialized_item, many=False):
        """
        Unlike the other data sinks, the User Retirement sink deletes records from the user PII tables in Clickhouse.

        Send delete queries to remove the serialized User from ClickHouse.
        """
        if many:
            users = serialized_item
        else:
            users = [serialized_item]
        user_ids = {str(user["user_id"]) for user in users}
        user_ids_str = ",".join(sorted(user_ids))
        clickhouse_pii_tables = getattr(
            settings, "EVENT_SINK_CLICKHOUSE_PII_MODELS", []
        )

        for table in clickhouse_pii_tables:
            params = {
                "query": f"ALTER TABLE {self.ch_database}.{table} DELETE WHERE user_id in ({user_ids_str})",
            }
            request = requests.Request(
                "POST",
                self.ch_url,
                params=params,
                auth=self.ch_auth,
            )
            self._send_clickhouse_request(request)
