"""
Helper functions for tests
"""

import csv
import json
import random
import string
from collections import namedtuple
from datetime import datetime, timedelta
from io import StringIO
from unittest.mock import MagicMock, Mock

from opaque_keys.edx.keys import CourseKey
from opaque_keys.edx.locator import BlockUsageLocator

ORIG_IMPORT = __import__
ORG = "testorg"
COURSE = "testcourse"
COURSE_RUN = "2023_Fall"

FakeCourse = namedtuple("FakeCourse", ["id"])
FakeCourseOverview = namedtuple("FakeCourseOverview", [
    # Key fields we keep at the top level
    "id",
    "org",
    "display_name",
    "start",
    "end",
    "enrollment_start",
    "enrollment_end",
    "self_paced",
    "created",
    "modified",
    # Fields we stuff in JSON
    "advertised_start",
    "announcement",
    "lowest_passing_grade",
    "invitation_only",
    "max_student_enrollments_allowed",
    "effort",
    "enable_proctored_exams",
    "entrance_exam_enabled",
    "external_id",
    "language",
])

FakeUser = namedtuple("FakeUser", ["id"])


class FakeXBlock:
    """
    Fakes the parameters of an XBlock that we care about.
    """
    def __init__(self, identifier, block_type="vertical", graded=False, completion_mode="unknown"):
        self.block_type = block_type
        self.scope_ids = Mock()
        self.scope_ids.usage_id.course_key = course_key_factory()
        self.scope_ids.block_type = self.block_type
        self.location = block_usage_locator_factory()
        self.display_name_with_default = f"Display name {identifier}"
        self.edited_on = datetime.now()
        self.children = []
        self.graded = graded
        self.completion_mode = completion_mode

    def get_children(self):
        """
        Fakes the method of the same name from an XBlock.
        """
        return self.children


def course_str_factory(course_id=None):
    """
    Return a valid course key string.
    """
    if not course_id:
        return f"course-v1:{ORG}+{COURSE}+{COURSE_RUN}"
    return f"course-v1:{ORG}+{course_id}+{COURSE_RUN}"


def course_key_factory():
    """
    Return a CourseKey object from our course key string.
    """
    return CourseKey.from_string(course_str_factory())


def block_usage_locator_factory():
    """
    Create a BlockUsageLocator with a random id.
    """
    block_id = ''.join(random.choices(string.ascii_letters, k=10))
    return BlockUsageLocator(course_key_factory(), block_type="category", block_id=block_id, deprecated=True)


def fake_course_overview_factory(modified=None):
    """
    Create a fake CourseOverview object with just the fields we care about.

    Modified is overridable, but can also be None.
    """
    return FakeCourseOverview(
        course_key_factory(),                  # id
        ORG,                                   # org
        "Test Course",                         # display_name
        datetime.now() - timedelta(days=90),   # start
        datetime.now() + timedelta(days=90),   # end
        datetime.now() - timedelta(days=90),   # enrollment_start
        datetime.now() + timedelta(days=90),   # enrollment_end
        False,                                 # self_paced
        datetime.now() - timedelta(days=180),  # created
        modified,                              # modified
        datetime.now() - timedelta(days=90),   # advertised_start
        datetime.now() - timedelta(days=90),   # announcement
        71.05,                                 # lowest_passing_grade
        False,                                 # invitation_only
        1000,                                  # max_student_enrollments_allowed
        "Pretty easy",                         # effort
        False,                                 # enable_proctored_exams
        True,                                  # entrance_exam_enabled
        "abcd1234",                            # external_id
        "Polish"                               # language
    )


def fake_serialize_fake_course_overview(course_overview):
    """
    Return a dict representation of a FakeCourseOverview.
    """
    json_fields = {
        "advertised_start": str(course_overview.advertised_start),
        "announcement": str(course_overview.announcement),
        "lowest_passing_grade": float(course_overview.lowest_passing_grade),
        "invitation_only": course_overview.invitation_only,
        "max_student_enrollments_allowed": course_overview.max_student_enrollments_allowed,
        "effort": course_overview.effort,
        "enable_proctored_exams": course_overview.enable_proctored_exams,
        "entrance_exam_enabled": course_overview.entrance_exam_enabled,
        "external_id": course_overview.external_id,
        "language": course_overview.language,
    }

    return {
        "org": course_overview.org,
        "course_key": str(course_overview.id),
        "display_name": course_overview.display_name,
        "course_start": course_overview.start,
        "course_end": course_overview.end,
        "enrollment_start": course_overview.enrollment_start,
        "enrollment_end": course_overview.enrollment_end,
        "self_paced": course_overview.self_paced,
        "course_data_json": json.dumps(json_fields),
        "created": course_overview.created,
        "modified": course_overview.modified,
        "dump_id": "",
        "time_last_dumped": "",
    }


def mock_course_overview():
    """
    Create a fake CourseOverview object that supports just the things we care about.
    """
    mock_overview = MagicMock()
    mock_overview.return_value = fake_course_overview_factory(datetime.now())
    return mock_overview


def mock_detached_xblock_types():
    """
    Mock the return results of xmodule.modulestore.store_utilities.DETACHED_XBLOCK_TYPES
    """
    # Current values as of 2023-05-01
    return {'static_tab', 'about', 'course_info'}


def get_clickhouse_http_params():
    """
    Get the params used in ClickHouse queries.
    """
    overview_params = {
        "input_format_allow_errors_num": 1,
        "input_format_allow_errors_ratio": 0.1,
        "query": "INSERT INTO cool_data.course_overviews FORMAT CSV"
    }
    blocks_params = {
        "input_format_allow_errors_num": 1,
        "input_format_allow_errors_ratio": 0.1,
        "query": "INSERT INTO cool_data.course_blocks FORMAT CSV"
    }

    return overview_params, blocks_params


def course_factory():
    """
    Return a fake course structure that exercises most of the serialization features.
    """
    # Create a base block
    top_block = FakeXBlock("top", block_type="course")
    course = [top_block, ]

    # Create a few sections
    for i in range(3):
        block = FakeXBlock(f"Section {i}", block_type="chapter")
        course.append(block)
        top_block.children.append(block)

        # Create some subsections
        if i > 0:
            for ii in range(3):
                sub_block = FakeXBlock(f"Subsection {ii}", block_type="sequential")
                course.append(sub_block)
                block.children.append(sub_block)

                for iii in range(3):
                    # Create some units
                    unit_block = FakeXBlock(f"Unit {iii}", block_type="vertical")
                    course.append(unit_block)
                    sub_block.children.append(unit_block)

    # Create some detached blocks at the top level
    for i in range(3):
        course.append(FakeXBlock(f"Detached {i}", block_type="course_info"))

    # Create some graded blocks at the top level
    for i in range(3):
        course.append(FakeXBlock(f"Graded {i}", graded=True))

    # Create some completable blocks at the top level
    course.append(FakeXBlock("Completable", completion_mode="completable"))
    course.append(FakeXBlock("Aggregator", completion_mode="aggregator"))
    course.append(FakeXBlock("Excluded", completion_mode="excluded"))

    return course


def check_overview_csv_matcher(course_overview):
    """
    Match the course overview CSV against the test course.

    This is a matcher for the "responses" library. It returns a function
    that actually does the matching.
    """
    def match(request):
        body = request.body

        f = StringIO(body.decode("utf-8"))
        reader = csv.reader(f)

        i = 0
        try:
            # The CSV should be in the same order as our course, make sure
            # everything matches
            for row in reader:
                assert row[0] == course_overview.org
                assert row[1] == str(course_overview.id)
                assert row[2] == course_overview.display_name
                assert row[3] == str(course_overview.start)
                assert row[4] == str(course_overview.end)
                assert row[5] == str(course_overview.enrollment_start)
                assert row[6] == str(course_overview.enrollment_end)
                assert row[7] == str(course_overview.self_paced)

                # Get our JSON string back out from the CSV, confirm that it's
                # real JSON, compare values
                dumped_json = json.loads(row[8])

                assert dumped_json["advertised_start"] == str(course_overview.advertised_start)
                assert dumped_json["announcement"] == str(course_overview.announcement)
                assert dumped_json["lowest_passing_grade"] == float(course_overview.lowest_passing_grade)
                assert dumped_json["invitation_only"] == course_overview.invitation_only
                assert dumped_json["max_student_enrollments_allowed"] == course_overview.max_student_enrollments_allowed
                assert dumped_json["effort"] == course_overview.effort
                assert dumped_json["enable_proctored_exams"] == course_overview.enable_proctored_exams
                assert dumped_json["entrance_exam_enabled"] == course_overview.entrance_exam_enabled
                assert dumped_json["external_id"] == course_overview.external_id
                assert dumped_json["language"] == course_overview.language

                assert row[9] == str(course_overview.created)
                assert row[10] == str(course_overview.modified)

                i += 1
        except EOFError as e:
            return False, f"Mismatch in row {i}: {e}"
        return True, ""
    return match


def check_block_csv_matcher(course):
    """
    Match the course structure CSV against the test course.

    This is a matcher for the "responses" library. It returns a function
    that actually does the matching.
    """
    def match(request):
        body = request.body.decode("utf-8")
        lines = body.split("\n")[:-1]

        # There should be one CSV line for each block in the test course
        if len(lines) != len(course):
            return False, f"Body has {len(lines)} lines, course has {len(course)}"

        f = StringIO(body)
        reader = csv.reader(f)

        i = 0
        try:
            # The CSV should be in the same order as our course, make sure
            # everything matches
            for row in reader:
                block = course[i]
                assert row[0] == block.location.org
                assert row[1] == str(block.location.course_key)
                assert row[2] == str(course[i].location)
                assert row[3] == block.display_name_with_default

                block_json_data = {
                    'course': block.location.course,
                    'run': block.location.run,
                    'block_type': str(block.block_type),
                }
                csv_json = json.loads(row[4])

                # Check some json data
                assert block_json_data["course"] == csv_json["course"]
                assert block_json_data["run"] == csv_json["run"]
                assert block_json_data["block_type"] == csv_json["block_type"]
                i += 1
        except AssertionError as e:
            return False, f"Mismatch in row {i}: {e}"
        return True, ""
    return match
