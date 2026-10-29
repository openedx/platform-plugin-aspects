"""
Tests for signal handlers.
"""

from unittest.mock import ANY, Mock, patch

from django.test import TestCase

from platform_plugin_aspects.signals import (
    on_catalog_pathway_deleted,
    on_catalog_pathway_saved_txn,
    on_externalid_saved_txn,
    on_pathway_enrollment_saved_txn,
    on_user_retirement,
    receive_course_publish,
)
from platform_plugin_aspects.sinks import CatalogPathwayTombstoneSink
from platform_plugin_aspects.sinks.user_retire_sink import UserRetirementSink


class SignalHandlersTestCase(TestCase):
    """
    Test cases for signal handlers.
    """

    @patch("platform_plugin_aspects.tasks.dump_course_to_clickhouse")
    def test_receive_course_publish(self, mock_dump_task):
        """
        Test that receive_course_publish calls dump_course_to_clickhouse.
        """
        sender = Mock()
        course_key = "sample_key"
        receive_course_publish(sender, course_key)

        mock_dump_task.delay.assert_called_once_with(course_key)

    @patch("platform_plugin_aspects.signals.transaction")
    def test_on_externalid_saved(self, mock_transaction):
        """
        Test that on_externalid_saved calls dump_data_to_clickhouse.
        """
        instance = Mock()
        sender = Mock()
        on_externalid_saved_txn(sender, instance)

        mock_transaction.on_commit.assert_called_once()

    @patch("platform_plugin_aspects.signals.transaction")
    def test_on_catalog_pathway_saved(self, mock_transaction):
        """
        Test that on_catalog_pathway_saved_txn defers the dump to on_commit.
        """
        instance = Mock()
        sender = Mock()
        on_catalog_pathway_saved_txn(sender, instance)

        mock_transaction.on_commit.assert_called_once()

    @patch("platform_plugin_aspects.signals.transaction")
    def test_on_pathway_enrollment_saved(self, mock_transaction):
        """
        Test that on_pathway_enrollment_saved_txn defers the dump to on_commit.
        """
        instance = Mock()
        sender = Mock()
        on_pathway_enrollment_saved_txn(sender, instance)

        mock_transaction.on_commit.assert_called_once()

    @patch("platform_plugin_aspects.tasks.dump_data_to_clickhouse")
    @patch("platform_plugin_aspects.signals.transaction")
    def test_on_catalog_pathway_deleted(self, mock_transaction, mock_dump_task):
        """
        Test that on_catalog_pathway_deleted queues the tombstone sink on commit, with the id
        read before Django clears it.
        """
        instance = Mock(id=7)
        on_catalog_pathway_deleted(Mock(), instance)
        instance.id = None

        mock_dump_task.delay.assert_not_called()
        mock_transaction.on_commit.assert_called_once_with(ANY, robust=True)
        mock_transaction.on_commit.call_args.args[0]()

        mock_dump_task.delay.assert_called_once_with(
            sink_module=CatalogPathwayTombstoneSink.__module__,
            sink_name="CatalogPathwayTombstoneSink",
            object_id="7",
        )

    @patch("platform_plugin_aspects.tasks.dump_data_to_clickhouse")
    def test_on_user_retirement(self, mock_dump_task):
        """
        Test that on_user_retirement calls dump_data_to_clickhouse
        """
        instance = Mock()
        sender = Mock()
        on_user_retirement(sender, instance)

        sink = UserRetirementSink(None, None)

        mock_dump_task.delay.assert_called_once_with(
            sink_module=sink.__module__,
            sink_name=sink.__class__.__name__,
            object_id=str(instance.id),
        )
