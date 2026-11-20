"""
Test the tag sink module.
"""

from unittest.mock import Mock, patch

from platform_plugin_aspects.sinks import TaxonomySink


@patch("platform_plugin_aspects.sinks.tag_sink.get_competency_api")
@patch("platform_plugin_aspects.sinks.ModelBaseSink.get_queryset")
def test_taxonomy_get_queryset(mock_get_queryset, mock_get_competency_api):
    """
    Test the taxonomy sink joins CompetencyTaxonomy through openedx-core's API.
    """
    api = Mock()
    mock_get_competency_api.return_value = api

    result = TaxonomySink(None, None).get_queryset()

    api.select_competency_taxonomies.assert_called_once_with(
        mock_get_queryset.return_value
    )
    assert result == api.select_competency_taxonomies.return_value


@patch("platform_plugin_aspects.sinks.tag_sink.get_competency_api", return_value=None)
@patch("platform_plugin_aspects.sinks.ModelBaseSink.get_queryset")
def test_taxonomy_get_queryset_without_cbe(mock_get_queryset, _):
    """
    Test the taxonomy sink still works when openedx-core has no competency taxonomies.
    """
    assert TaxonomySink(None, None).get_queryset() == mock_get_queryset.return_value
