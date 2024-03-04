"""
Tests for the user_retire sinks.
"""

import logging
from unittest.mock import patch

import responses
from django.test.utils import override_settings
from responses.registries import OrderedRegistry

from platform_plugin_aspects.sinks import UserRetirementSink
from platform_plugin_aspects.tasks import dump_data_to_clickhouse
from test_utils.helpers import FakeUser

log = logging.getLogger(__name__)


@responses.activate(  # pylint: disable=unexpected-keyword-arg,no-value-for-parameter
    registry=OrderedRegistry
)
@override_settings(EVENT_SINK_CLICKHOUSE_PII_MODELS=["user_profile", "external_id"])
@patch("platform_plugin_aspects.sinks.UserRetirementSink.serialize_item")
@patch("platform_plugin_aspects.sinks.UserRetirementSink.is_enabled")
@patch("platform_plugin_aspects.sinks.UserRetirementSink.get_model")
def test_retire_user(mock_user_model, mock_is_enabled, mock_serialize_item):
    """
    Test of a successful user retirement.
    """
    # Create a fake user
    user = FakeUser(246)
    mock_user_model.return_value.get_from_id.return_value = user
    mock_is_enabled.return_value = True
    mock_serialize_item.return_value = {"user_id": user.id}

    # Use the responses library to catch the POSTs to ClickHouse
    # and match them against the expected values
    user_profile_delete = responses.post(
        "https://foo.bar/",
        match=[
            responses.matchers.query_param_matcher(
                {
                    "query": f"ALTER TABLE cool_data.user_profile DELETE WHERE user_id in ({user.id})",
                }
            )
        ],
    )
    external_id_delete = responses.post(
        "https://foo.bar/",
        match=[
            responses.matchers.query_param_matcher(
                {
                    "query": f"ALTER TABLE cool_data.external_id DELETE WHERE user_id in ({user.id})",
                }
            )
        ],
    )

    sink = UserRetirementSink(None, None)
    dump_data_to_clickhouse(
        sink_module=sink.__module__,
        sink_name=sink.__class__.__name__,
        object_id=user.id,
    )

    assert mock_user_model.call_count == 1
    assert mock_is_enabled.call_count == 1
    assert mock_serialize_item.call_count == 1
    assert user_profile_delete.call_count == 1
    assert external_id_delete.call_count == 1


@responses.activate(  # pylint: disable=unexpected-keyword-arg,no-value-for-parameter
    registry=OrderedRegistry
)
@override_settings(EVENT_SINK_CLICKHOUSE_PII_MODELS=["user_profile"])
@patch("platform_plugin_aspects.sinks.UserRetirementSink.serialize_item")
def test_retire_many_users(mock_serialize_item):
    """
    Test of a successful "many users" retirement.
    """
    # Create and serialize a few fake users
    users = (FakeUser(246), FakeUser(22), FakeUser(91))
    mock_serialize_item.return_value = [{"user_id": user.id} for user in users]

    # Use the responses library to catch the POSTs to ClickHouse
    # and match them against the expected values
    user_profile_delete = responses.post(
        "https://foo.bar/",
        match=[
            responses.matchers.query_param_matcher(
                {
                    "query": "ALTER TABLE cool_data.user_profile DELETE WHERE user_id in (22,246,91)",
                }
            )
        ],
    )

    sink = UserRetirementSink(None, log)
    sink.dump(
        item_id=users[0].id,
        many=True,
    )

    assert mock_serialize_item.call_count == 1
    assert user_profile_delete.call_count == 1
