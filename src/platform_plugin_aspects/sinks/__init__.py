"""
This module contains the sinks for the platform plugin aspects.
"""

from .base_sink import BaseSink, ModelBaseSink
from .course_enrollment_sink import CourseEnrollmentSink
from .course_overview_sink import CourseOverviewSink, XBlockSink
from .external_id_sink import ExternalIdSink
from .tag_sink import ObjectTagSink, TagSink, TaxonomySink
from .user_profile_sink import UserProfileSink
from .user_retire_sink import UserRetirementSink
