"""
Test the external_id_sink module.
"""

from unittest.mock import patch

from platform_plugin_aspects.sinks.external_id_sink import ExternalIdSink


@patch("platform_plugin_aspects.sinks.external_id_sink.ModelBaseSink.get_queryset")
def test_get_queryset(mock_get_queryset):
    """
    Test the get_queryset method.
    """
    sink = ExternalIdSink(None, None)

    sink.get_queryset()

    mock_get_queryset.assert_called_once_with(None)
    mock_get_queryset.return_value.select_related.assert_called_once_with("user", "external_id_type")
