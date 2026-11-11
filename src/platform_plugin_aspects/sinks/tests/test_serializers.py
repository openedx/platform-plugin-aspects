import json
from datetime import datetime
from unittest.mock import Mock, patch

from django.test import TestCase

from platform_plugin_aspects.sinks.serializers import (
    BaseSinkSerializer,
    CatalogPathwaySerializer,
    CourseOverviewSerializer,
    DateTimeJSONEncoder,
    PathwayEnrollmentSerializer,
    StudentCompetencyCriteriaGroupStatusSerializer,
    StudentCompetencyStatusSerializer,
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


class TestCatalogPathwaySerializer(TestCase):
    """
    Test CatalogPathwaySerializer
    """

    def test_is_deleted(self):
        """
        Test that saved pathways are written with is_deleted 0, in the last column.
        """
        serializer = CatalogPathwaySerializer()

        self.assertEqual(serializer.get_is_deleted(Mock()), 0)
        self.assertEqual(CatalogPathwaySerializer.Meta.fields[-1], "is_deleted")


class TestPathwayEnrollmentSerializer(TestCase):
    """
    Test PathwayEnrollmentSerializer
    """

    @patch("platform_plugin_aspects.sinks.serializers.get_or_create_xapi_actor_id")
    def test_get_actor_id(self, mock_get_or_create_xapi_actor_id):
        """
        Test that the learner is serialized as their xAPI actor id.
        """
        mock_get_or_create_xapi_actor_id.return_value = (
            "29e5b22b-b457-49fa-9633-6c0123305d18"
        )
        enrollment = Mock()

        actor_id = PathwayEnrollmentSerializer().get_actor_id(enrollment)

        assert actor_id == "29e5b22b-b457-49fa-9633-6c0123305d18"
        mock_get_or_create_xapi_actor_id.assert_called_once_with(enrollment.user)


class TestStudentCompetencyStatusSerializer(TestCase):
    """
    Test StudentCompetencyStatusSerializer
    """

    @patch("platform_plugin_aspects.sinks.serializers.get_or_create_xapi_actor_id")
    def test_get_actor_id(self, mock_get_xapi_actor_id):
        """
        Test that the learner is serialized as their xAPI actor id.
        """
        mock_get_xapi_actor_id.return_value = "29e5b22b-b457-49fa-9633-6c0123305d18"
        status = Mock()

        actor_id = StudentCompetencyStatusSerializer().get_actor_id(status)

        assert actor_id == "29e5b22b-b457-49fa-9633-6c0123305d18"
        mock_get_xapi_actor_id.assert_called_once_with(status.user)


class TestStudentCompetencyCriteriaGroupStatusSerializer(TestCase):
    """
    Test StudentCompetencyCriteriaGroupStatusSerializer
    """

    def setUp(self):
        self.serializer = StudentCompetencyCriteriaGroupStatusSerializer()
        # "parent" is a Mock constructor argument, so it is set as an attribute.
        self.root = Mock(parent_id=None, course_id=None)
        self.root.parent = None
        self.course_group = Mock(parent_id=1, course_id=7)
        self.course_group.parent = self.root
        self.course_group.course.course_key = "course-v1:Org+Course+Run"
        self.leaf = Mock(parent_id=2, course_id=None)
        self.leaf.parent = self.course_group

    def test_group_level(self):
        """
        Test that groups are serialized as root, course or leaf.
        """
        levels = [
            self.serializer.get_group_level(Mock(group=group))
            for group in (self.root, self.course_group, self.leaf)
        ]

        assert levels == ["root", "course", "leaf"]

    def test_course_key(self):
        """
        Test that a leaf takes its course group's course key and a root has none.
        """
        assert (
            self.serializer.get_course_key(Mock(group=self.course_group))
            == "course-v1:Org+Course+Run"
        )
        assert (
            self.serializer.get_course_key(Mock(group=self.leaf))
            == "course-v1:Org+Course+Run"
        )
        assert self.serializer.get_course_key(Mock(group=self.root)) == ""

    @patch("platform_plugin_aspects.sinks.serializers.get_or_create_xapi_actor_id")
    def test_get_actor_id(self, mock_get_or_create_xapi_actor_id):
        """
        Test that the learner is serialized as their xAPI actor id.
        """
        mock_get_or_create_xapi_actor_id.return_value = "29e5b22b-b457-49fa-9633-6c0123305d18"
        status = Mock()

        assert (
            self.serializer.get_actor_id(status)
            == "29e5b22b-b457-49fa-9633-6c0123305d18"
        )
        mock_get_or_create_xapi_actor_id.assert_called_once_with(status.user)
