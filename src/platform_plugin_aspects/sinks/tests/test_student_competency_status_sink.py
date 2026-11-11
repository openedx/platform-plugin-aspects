"""
Test the student competency status sink module.
"""

from unittest.mock import patch

from platform_plugin_aspects.sinks import (
    StudentCompetencyCriteriaGroupStatusSink,
    StudentCompetencyStatusSink,
)


@patch("platform_plugin_aspects.sinks.ModelBaseSink.get_queryset")
def test_get_queryset(mock_get_queryset):
    """
    Test the get_queryset method.
    """
    sink = StudentCompetencyStatusSink(None, None)

    sink.get_queryset()

    mock_get_queryset.assert_called_once_with(None)
    mock_get_queryset.return_value.select_related.assert_called_once_with(
        "user", "tag", "status"
    )


@patch("platform_plugin_aspects.sinks.ModelBaseSink.get_queryset")
def test_group_status_get_queryset(mock_get_queryset):
    """
    Test the group status sink loads the group's tag and course with each row.
    """
    sink = StudentCompetencyCriteriaGroupStatusSink(None, None)

    sink.get_queryset()

    mock_get_queryset.assert_called_once_with(None)
    mock_get_queryset.return_value.select_related.assert_called_once_with(
        "user", "status", "group__tag", "group__course"
    )
