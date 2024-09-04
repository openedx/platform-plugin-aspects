"""Tag sink"""

from platform_plugin_aspects.sinks.base_sink import ModelBaseSink
from platform_plugin_aspects.sinks.serializers import (
    ObjectTagSerializer,
    TagSerializer,
    TaxonomySerializer,
)


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
