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
    StudentCompetencyCourseStatusSerializer,
    StudentCompetencyStatusSerializer,
    TaxonomySerializer,
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

    def test_fields(self):
        """
        Test the exact field order: sink inserts are positional, so it is the ClickHouse column order.
        """
        assert StudentCompetencyStatusSerializer.Meta.fields == [
            "id",
            "actor_id",
            "tag_id",
            "taxonomy_id",
            "status_id",
            "status_name",
            "created",
            "modified",
            "dump_id",
            "time_last_dumped",
        ]

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


class TestStudentCompetencyCourseStatusSerializer(TestCase):
    """
    Test StudentCompetencyCourseStatusSerializer
    """

    def setUp(self):
        self.serializer = StudentCompetencyCourseStatusSerializer()

    def test_fields(self):
        """
        Test the exact field order: sink inserts are positional, so it is the ClickHouse column order.

        The row carries the group's competency and course, and no group tree
        (no parent_group_id or group_level).
        """
        assert self.serializer.Meta.fields == [
            "id",
            "actor_id",
            "group_id",
            "tag_id",
            "taxonomy_id",
            "course_key",
            "status_id",
            "status_name",
            "created",
            "modified",
            "dump_id",
            "time_last_dumped",
        ]

    @patch("platform_plugin_aspects.sinks.serializers.get_or_create_xapi_actor_id")
    def test_get_actor_id(self, mock_get_or_create_xapi_actor_id):
        """
        Test that the learner is serialized as their xAPI actor id.
        """
        mock_get_or_create_xapi_actor_id.return_value = (
            "29e5b22b-b457-49fa-9633-6c0123305d18"
        )
        status = Mock()

        assert (
            self.serializer.get_actor_id(status)
            == "29e5b22b-b457-49fa-9633-6c0123305d18"
        )
        mock_get_or_create_xapi_actor_id.assert_called_once_with(status.user)


class TestTaxonomySerializer(TestCase):
    """
    Test TaxonomySerializer
    """

    def test_taxonomy_type_is_last(self):
        """
        Test that taxonomy_type is the last field, matching the ClickHouse column order.
        """
        assert TaxonomySerializer.Meta.fields[-1] == "taxonomy_type"

    @patch("platform_plugin_aspects.sinks.serializers.get_competency_api")
    def test_taxonomy_type(self, mock_get_competency_api):
        """
        Test that the type comes from openedx-core's is_competency_taxonomy.
        """
        api = mock_get_competency_api.return_value
        api.is_competency_taxonomy.return_value = True
        assert TaxonomySerializer().get_taxonomy_type(Mock()) == "competency"
        api.is_competency_taxonomy.return_value = False
        assert TaxonomySerializer().get_taxonomy_type(Mock()) == "tags"

    @patch(
        "platform_plugin_aspects.sinks.serializers.get_competency_api",
        return_value=None,
    )
    def test_taxonomy_type_without_cbe(self, _):
        """
        Test that every taxonomy is "tags" when openedx-core has no competency taxonomies.
        """
        assert TaxonomySerializer().get_taxonomy_type(Mock()) == "tags"
