"""Django serializers for the event_sink_clickhouse app."""

import json
import uuid
from datetime import date, datetime

from django.utils import timezone
from pytz import UTC
from rest_framework import serializers

from platform_plugin_aspects.utils import get_model, get_tags_for_block


class DateTimeJSONEncoder(json.JSONEncoder):
    """JSON encoder aware of datetime.datetime and datetime.date objects"""

    def default(self, obj):  # pylint: disable=arguments-renamed
        """
        Serialize datetime and date objects of iso format.

        datetime objects are converted to UTC.
        """

        if isinstance(obj, datetime):
            if obj.tzinfo is None:
                # Localize to UTC naive datetime objects
                obj = UTC.localize(obj)  # pylint: disable=no-value-for-parameter
            else:
                # Convert to UTC datetime objects from other timezones
                obj = obj.astimezone(UTC)
            return obj.isoformat()
        elif isinstance(obj, date):
            return obj.isoformat()

        return super().default(obj)


class BaseSinkSerializer(serializers.Serializer):  # pylint: disable=abstract-method
    """Base sink serializer for ClickHouse."""

    dump_id = serializers.SerializerMethodField()
    time_last_dumped = serializers.SerializerMethodField()

    class Meta:
        """Meta class for base sink serializer."""

        fields = [
            "dump_id",
            "time_last_dumped",
        ]

    def get_dump_id(self, instance):  # pylint: disable=unused-argument
        """Return a unique ID for the dump."""
        return uuid.uuid4()

    def get_time_last_dumped(self, instance):  # pylint: disable=unused-argument
        """Return the timestamp for the dump."""
        return timezone.now()


class UserProfileSerializer(BaseSinkSerializer, serializers.ModelSerializer):
    """Serializer for user profile events."""

    email = serializers.CharField(source="user.email")

    class Meta:
        """Meta class for user profile serializer."""

        model = get_model("user_profile")

        fields = [
            "id",
            "user_id",
            "name",
            "email",
            "meta",
            "courseware",
            "language",
            "location",
            "year_of_birth",
            "gender",
            "level_of_education",
            "mailing_address",
            "city",
            "country",
            "state",
            "goals",
            "bio",
            "profile_image_uploaded_at",
            "phone_number",
            "dump_id",
            "time_last_dumped",
        ]


class UserExternalIDSerializer(BaseSinkSerializer, serializers.ModelSerializer):
    """Serializer for user external ID events."""

    external_id_type = serializers.CharField(source="external_id_type.name")
    username = serializers.CharField(source="user.username")

    class Meta:
        """Meta class for user external ID serializer."""

        model = get_model("external_id")
        fields = [
            "external_user_id",
            "external_id_type",
            "username",
            "user_id",
            "dump_id",
            "time_last_dumped",
        ]


class UserRetirementSerializer(BaseSinkSerializer, serializers.ModelSerializer):
    """Serializer for user retirement events."""

    user_id = serializers.CharField(source="id")

    class Meta:
        """Meta class for user retirement serializer."""

        model = get_model("auth_user")
        fields = [
            "user_id",
        ]


class CourseOverviewSerializer(BaseSinkSerializer, serializers.ModelSerializer):
    """Serializer for course overview events."""

    course_data_json = serializers.SerializerMethodField()
    course_key = serializers.SerializerMethodField()
    course_start = serializers.CharField(source="start")
    course_end = serializers.CharField(source="end")

    class Meta:
        """Meta classes for course overview serializer."""

        model = get_model("course_overviews")
        fields = [
            "org",
            "course_key",
            "display_name",
            "course_start",
            "course_end",
            "enrollment_start",
            "enrollment_end",
            "self_paced",
            "course_data_json",
            "created",
            "modified",
            "dump_id",
            "time_last_dumped",
        ]

    def get_course_data_json(self, overview):
        """Return the course data as a JSON string."""
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
            "tags": get_tags_for_block(overview.id),
        }
        return json.dumps(json_fields, cls=DateTimeJSONEncoder)

    def get_course_key(self, overview):
        """Return the course key as a string."""
        return str(overview.id)


class CourseEnrollmentSerializer(BaseSinkSerializer, serializers.ModelSerializer):
    """Serializer for the Course Enrollment model."""

    course_key = serializers.SerializerMethodField()
    username = serializers.CharField(source="user.username")

    class Meta:
        """Meta class for the CourseEnrollmentSerializer"""

        model = get_model("course_enrollment")
        fields = [
            "id",
            "course_key",
            "created",
            "is_active",
            "mode",
            "username",
            "user_id",
            "dump_id",
            "time_last_dumped",
        ]

    def get_course_key(self, obj):
        """Return the course key as a string."""
        return str(obj.course_id)


class TagSerializer(BaseSinkSerializer, serializers.ModelSerializer):
    """Serializer for the Tag model."""

    lineage = serializers.SerializerMethodField()

    class Meta:
        """Meta class for the TagSerializer."""

        model = get_model("tag")
        fields = [
            "id",
            "taxonomy",
            "parent",
            "value",
            "external_id",
            "lineage",
            "dump_id",
            "time_last_dumped",
        ]

    def get_lineage(self, instance):
        return json.dumps(instance.get_lineage())


class ObjectTagSerializer(BaseSinkSerializer, serializers.ModelSerializer):
    """Serializer for the ObjectTag model."""

    lineage = serializers.SerializerMethodField()

    class Meta:
        """Meta class for the ObjectTagSerializer"""

        model = get_model("object_tag")
        fields = [
            "id",
            "object_id",
            "taxonomy",
            "tag",
            "_value",
            "_export_id",
            "lineage",
            "dump_id",
            "time_last_dumped",
        ]

    def get_lineage(self, instance):
        return json.dumps(instance.get_lineage())


class TaxonomySerializer(BaseSinkSerializer, serializers.ModelSerializer):
    """Serializer for the Taxonomy model."""

    class Meta:
        """Meta class for the TaxonomySerializer."""

        model = get_model("taxonomy")
        fields = [
            "id",
            "name",
            "dump_id",
            "time_last_dumped",
        ]
