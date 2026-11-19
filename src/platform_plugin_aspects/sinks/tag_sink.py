"""Tag sink"""

from platform_plugin_aspects.sinks.base_sink import ModelBaseSink
from platform_plugin_aspects.sinks.serializers import (
    ObjectTagSerializer,
    TagSerializer,
    TaxonomySerializer,
)
from platform_plugin_aspects.utils import get_competency_api


class TagSink(ModelBaseSink):  # pylint: disable=abstract-method
    """
    Sink for content tags
    """

    model = "tag"
    unique_key = "id"
    clickhouse_table_name = "tag"
    timestamp_field = "time_last_dumped"
    name = "Tag"
    serializer_class = TagSerializer


class TaxonomySink(ModelBaseSink):  # pylint: disable=abstract-method
    """
    Sink for content taxonomy
    """

    model = "taxonomy"
    unique_key = "id"
    clickhouse_table_name = "taxonomy"
    timestamp_field = "time_last_dumped"
    name = "Taxonomy"
    serializer_class = TaxonomySerializer

    def get_queryset(self, start_pk=None):
        """Join each taxonomy's CompetencyTaxonomy row, so taxonomy_type costs no query per row."""
        queryset = super().get_queryset(start_pk)
        competency_api = get_competency_api()
        if competency_api is None:
            return queryset
        return competency_api.select_competency_taxonomies(queryset)


class ObjectTagSink(ModelBaseSink):  # pylint: disable=abstract-method
    """
    Sink for tagged objects
    """

    model = "object_tag"
    unique_key = "id"
    clickhouse_table_name = "object_tag"
    timestamp_field = "time_last_dumped"
    name = "ObjectTag"
    serializer_class = ObjectTagSerializer
