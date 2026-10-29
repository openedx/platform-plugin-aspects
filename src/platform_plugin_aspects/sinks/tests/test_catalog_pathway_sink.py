"""
Test the catalog pathway sink module.
"""

import logging
from unittest.mock import Mock, patch

import pytest
import requests
import responses
from responses.registries import OrderedRegistry

from platform_plugin_aspects.sinks import (
    CatalogPathwaySink,
    CatalogPathwayTombstoneSink,
)

log = logging.getLogger(__name__)


@patch("platform_plugin_aspects.sinks.ModelBaseSink.get_queryset")
def test_get_queryset(mock_get_queryset):
    """
    Test the get_queryset method.
    """
    sink = CatalogPathwaySink(None, None)

    sink.get_queryset()

    mock_get_queryset.assert_called_once_with(None)
    mock_get_queryset.return_value.select_related.assert_called_once_with(
        "org", "category"
    )


@responses.activate(  # pylint: disable=unexpected-keyword-arg,no-value-for-parameter
    registry=OrderedRegistry
)
def test_tombstone_dump():
    """
    Test that the tombstone sink copies the pathway's latest row with is_deleted set.
    """
    tombstone = responses.post(
        "https://foo.bar/",
        match=[
            responses.matchers.query_param_matcher(
                {
                    "query": "INSERT INTO cool_data.catalog_pathway "
                    "SELECT * REPLACE (1 AS is_deleted, generateUUIDv4() AS dump_id, "
                    "now64(6) AS time_last_dumped) "
                    "FROM (SELECT * FROM cool_data.catalog_pathway WHERE id = 7 "
                    "ORDER BY time_last_dumped DESC LIMIT 1)",
                }
            )
        ],
        headers={"X-ClickHouse-Summary": '{"written_rows":"1"}'},
    )
    mock_log = Mock()

    CatalogPathwayTombstoneSink(None, mock_log).dump("7")

    assert tombstone.call_count == 1
    mock_log.warning.assert_not_called()


@responses.activate(  # pylint: disable=unexpected-keyword-arg,no-value-for-parameter
    registry=OrderedRegistry
)
def test_tombstone_dump_retries_once():
    """
    Test that a failed tombstone is retried once, and a second failure raises.
    """
    responses.post("https://foo.bar/", body=requests.ConnectionError())
    responses.post("https://foo.bar/")

    CatalogPathwayTombstoneSink(None, log).dump("7")

    responses.post("https://foo.bar/", body=requests.ConnectionError())
    responses.post("https://foo.bar/", body=requests.ConnectionError())

    with pytest.raises(requests.ConnectionError):
        CatalogPathwayTombstoneSink(None, log).dump("7")


@responses.activate  # pylint: disable=unexpected-keyword-arg,no-value-for-parameter
def test_tombstone_dump_warns_when_nothing_written():
    """
    Test that a pathway that was never dumped logs a warning.
    """
    responses.post(
        "https://foo.bar/",
        headers={"X-ClickHouse-Summary": '{"written_rows":"0"}'},
    )
    mock_log = Mock()

    CatalogPathwayTombstoneSink(None, mock_log).dump("7")

    mock_log.warning.assert_called_once()


def test_tombstone_dump_rejects_non_integer_id():
    """
    Test that an id that isn't an integer never reaches the query.
    """
    with pytest.raises(ValueError):
        CatalogPathwayTombstoneSink(None, log).dump("1 OR 1=1")
