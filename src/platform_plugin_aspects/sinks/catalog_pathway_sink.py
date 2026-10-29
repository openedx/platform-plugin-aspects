"""Catalog Pathway sink"""

import json

import requests

from platform_plugin_aspects.sinks.base_sink import ModelBaseSink
from platform_plugin_aspects.sinks.serializers import CatalogPathwaySerializer


class CatalogPathwaySink(ModelBaseSink):  # pylint: disable=abstract-method
    """
    Sink for the openedx-core CatalogPathway model
    """

    model = "catalog_pathway"
    unique_key = "id"
    clickhouse_table_name = "catalog_pathway"
    timestamp_field = "time_last_dumped"
    name = "Catalog Pathway"
    serializer_class = CatalogPathwaySerializer

    # Unlike the other sink tables, time_last_dumped is DateTime64 here because it is the
    # ReplacingMergeTree version column; the serializer writes it with a UTC offset, which
    # only "best_effort" parses.
    CLICKHOUSE_BULK_INSERT_PARAMS = {
        **ModelBaseSink.CLICKHOUSE_BULK_INSERT_PARAMS,
        "date_time_input_format": "best_effort",
    }

    def get_queryset(self, start_pk=None):
        return super().get_queryset(start_pk).select_related("org", "category")


# pylint: disable-next=abstract-method
class CatalogPathwayTombstoneSink(CatalogPathwaySink):
    """
    Sink for deleted openedx-core CatalogPathways

    The pathway is gone from MySQL by the time this runs, so instead of serializing it, the
    pathway's latest row in ClickHouse is copied with is_deleted set. A pathway that was never
    dumped gets no row.
    """

    name = "Catalog Pathway Tombstone"

    def dump(self, item_id, many=False, initial=None):
        """
        Write a tombstone row for the deleted pathway with id item_id.
        """
        table = f"{self.ch_database}.{self.clickhouse_table_name}"
        params = {
            "query": (
                f"INSERT INTO {table} "
                "SELECT * REPLACE (1 AS is_deleted, generateUUIDv4() AS dump_id, "
                "now64(6) AS time_last_dumped) "
                # Picked in a subquery: next to the REPLACE, ORDER BY time_last_dumped would
                # resolve to the now64(6) alias and copy an arbitrary version.
                f"FROM (SELECT * FROM {table} WHERE id = {int(item_id)} "
                "ORDER BY time_last_dumped DESC LIMIT 1)"
            ),
        }
        request = requests.Request(
            "POST",
            self.ch_url,
            params=params,
            auth=self.ch_auth,
        )
        self.log.info(f"Now dumping {self.name} {item_id} to ClickHouse")
        # Retried once: the pathway is gone from MySQL, so a lost tombstone can't be backfilled.
        try:
            response = self._send_clickhouse_request(request)
        except requests.RequestException:
            response = self._send_clickhouse_request(request)
        summary = json.loads(response.headers.get("X-ClickHouse-Summary", "{}"))
        if summary.get("written_rows") == "0":
            self.log.warning(
                f"No {self.name} written for {item_id}, it was never dumped"
            )
        self.log.info(f"Completed dumping {self.name} {item_id} to ClickHouse")
