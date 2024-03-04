"""
Test the external_id_sink module.
"""

from unittest.mock import patch

from platform_plugin_aspects.sinks.user_profile_sink import UserProfileSink


@patch("platform_plugin_aspects.sinks.ModelBaseSink.get_queryset")
def test_get_queryset(mock_get_queryset):
    """
    Test the get_queryset method.
    """
    sink = UserProfileSink(None, None)

    sink.get_queryset()

    mock_get_queryset.assert_called_once_with(None)
    mock_get_queryset.return_value.select_related.assert_called_once_with("user")
