"""
Test the student competency status sink module.
"""

from unittest.mock import Mock, patch

from platform_plugin_aspects.sinks import (
    StudentCompetencyCourseStatusSink,
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
    Test the group status sink keeps course-level groups and loads their tag and course.
    """
    sink = StudentCompetencyCourseStatusSink(None, None)

    sink.get_queryset()

    mock_get_queryset.assert_called_once_with(None)
    mock_get_queryset.return_value.filter.assert_called_once_with(
        group__course__isnull=False
    )
    mock_get_queryset.return_value.filter.return_value.select_related.assert_called_once_with(
        "user", "status", "group__tag", "group__course"
    )


@patch.object(StudentCompetencyStatusSink, "get_queryset")
def test_status_get_object(mock_get_queryset):
    """
    Test a single dump goes through get_queryset, so it loads the row's user, tag and status in one query.
    """
    sink = StudentCompetencyStatusSink(None, None)

    result = sink.get_object(7)

    mock_get_queryset.return_value.get.assert_called_once_with(id=7)
    assert result == mock_get_queryset.return_value.get.return_value


@patch.object(StudentCompetencyCourseStatusSink, "get_queryset")
def test_course_status_get_object(mock_get_queryset):
    """
    Test a single dump goes through get_queryset, so it skips root and leaf groups too.
    """
    sink = StudentCompetencyCourseStatusSink(None, None)

    result = sink.get_object(7)

    mock_get_queryset.return_value.get.assert_called_once_with(id=7)
    assert result == mock_get_queryset.return_value.get.return_value


def test_is_course_level():
    """
    Test only statuses of groups with a course run are course-level.
    """
    assert StudentCompetencyCourseStatusSink.is_course_level(
        Mock(group=Mock(course_id=3))
    )
    assert not StudentCompetencyCourseStatusSink.is_course_level(
        Mock(group=Mock(course_id=None))
    )
