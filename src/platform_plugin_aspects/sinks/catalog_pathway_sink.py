"""Catalog Pathway sink"""

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

    def get_queryset(self, start_pk=None):
        return super().get_queryset(start_pk).select_related("org", "category")
