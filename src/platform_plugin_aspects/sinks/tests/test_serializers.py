import json
from datetime import datetime
from unittest.mock import Mock, patch

from django.test import TestCase

from platform_plugin_aspects.sinks.serializers import (
    BaseSinkSerializer,
    CourseOverviewSerializer,
    DateTimeJSONEncoder,
)
from test_utils.helpers import course_key_factory


class TestBaseSinkSerializer(TestCase):
    """
    Test BaseSinkSerializer
    """

    def setUp(self):
        self.serializer = BaseSinkSerializer()

    def test_to_representation(self):
        """
        Test to_representation
        """
        self.assertEqual(
            list(self.serializer.to_representation({}).keys()),
            ["dump_id", "time_last_dumped"],
        )


class TestCourseOverviewSerializer(TestCase):
    """
    Test CourseOverviewSerializer
    """

    def setUp(self):
        self.serializer = CourseOverviewSerializer()

    @patch("platform_plugin_aspects.sinks.serializers.get_tags_for_block")
    def test_get_course_data_json(self, mock_get_tags):
        """
        Test to_representation

        json_fields = {
            "advertised_start": getattr(overview, "advertised_start", ""),
            "announcement": getattr(overview, "announcement", ""),
            "lowest_passing_grade": float(
                getattr(overview, "lowest_passing_grade", 0.0)
            ),
            "invitation_only": getattr(overview, "invitation_only", ""),
            "max_student_enrollments_allowed": getattr(
                overview, "max_student_enrollments_allowed", None
            ),
            "effort": getattr(overview, "effort", ""),
            "enable_proctored_exams": getattr(overview, "enable_proctored_exams", ""),
            "entrance_exam_enabled": getattr(overview, "entrance_exam_enabled", ""),
            "external_id": getattr(overview, "external_id", ""),
            "language": getattr(overview, "language", ""),
        }
        """
        expected_tags = ["TAX1=tag1", "TAX2=tag2"]
        json_fields = {
            "advertised_start": datetime.now(),
            "announcement": "announcement",
            "lowest_passing_grade": 0.0,
            "invitation_only": "invitation_only",
            "max_student_enrollments_allowed": None,
            "effort": "effort",
            "enable_proctored_exams": "enable_proctored_exams",
            "entrance_exam_enabled": "entrance_exam_enabled",
            "external_id": "external_id",
            "language": "language",
            "tags": expected_tags,
        }
        mock_overview = Mock(**json_fields)
        mock_overview.id = course_key_factory()

        # Fake the "get_tags_for_course" api since we can't import it here
        mock_course_block = Mock(location=mock_overview.id)
        mock_get_tags.return_value = expected_tags

        self.assertEqual(
            self.serializer.get_course_data_json(mock_overview),
            json.dumps(json_fields, cls=DateTimeJSONEncoder),
        )
        mock_get_tags.assert_called_once_with(mock_overview.id)

    def test_get_course_key(self):
        """
        Test get_course_key
        """
        mock_id = Mock()
        mock_overview = Mock(id=mock_id)
        self.assertEqual(self.serializer.get_course_key(mock_overview), str(mock_id))
