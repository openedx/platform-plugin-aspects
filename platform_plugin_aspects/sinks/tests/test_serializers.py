import json
from unittest.mock import Mock

from django.test import TestCase

from platform_plugin_aspects.sinks.serializers import (
    BaseSinkSerializer,
    CourseOverviewSerializer,
)


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

    def test_get_course_data_json(self):
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
        json_fields = {
            "advertised_start": "2018-01-01T00:00:00Z",
            "announcement": "announcement",
            "lowest_passing_grade": 0.0,
            "invitation_only": "invitation_only",
            "max_student_enrollments_allowed": None,
            "effort": "effort",
            "enable_proctored_exams": "enable_proctored_exams",
            "entrance_exam_enabled": "entrance_exam_enabled",
            "external_id": "external_id",
            "language": "language",
        }
        mock_overview = Mock(**json_fields)
        self.assertEqual(
            self.serializer.get_course_data_json(mock_overview), json.dumps(json_fields)
        )

    def test_get_course_key(self):
        """
        Test get_course_key
        """
        mock_id = Mock()
        mock_overview = Mock(id=mock_id)
        self.assertEqual(self.serializer.get_course_key(mock_overview), str(mock_id))
