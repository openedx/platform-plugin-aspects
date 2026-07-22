"""
Handler for the CMS COURSE_PUBLISHED event

Does the following:
- Pulls the course structure from modulestore
- Serialize the xblocks
- Sends them to ClickHouse in CSV format

Note that the serialization format does not include all fields as there may be things like
LTI passwords and other secrets. We just take the fields necessary for reporting at this time.
"""

import datetime
import json

from opaque_keys.edx.keys import CourseKey

from platform_plugin_aspects.sinks.base_sink import ModelBaseSink
from platform_plugin_aspects.sinks.serializers import CourseOverviewSerializer
from platform_plugin_aspects.utils import (
    get_detached_xblock_types,
    get_modulestore,
    get_tags_for_block,
)

# Defaults we want to ensure we fail early on bulk inserts
CLICKHOUSE_BULK_INSERT_PARAMS = {
    "input_format_allow_errors_num": 1,
    "input_format_allow_errors_ratio": 0.1,
}

MODULESTORE_PUBLISHED_ONLY_FLAG = "rev-opt-published-only"


class XBlockSink(ModelBaseSink):
    """
    Sink for XBlock model
    """

    unique_key = "location"
    clickhouse_table_name = "course_blocks"
    timestamp_field = "time_last_dumped"
    name = "XBlock"
    nested_sinks = []

    def dump_related(self, serialized_item, dump_id, time_last_dumped):
        """Dump all XBlocks for a course"""
        self.dump(
            serialized_item,
            many=True,
            initial={"dump_id": dump_id, "time_last_dumped": time_last_dumped},
        )

    def get_xblocks_recursive(self, parent_block, detached_xblock_types, initial):
        """
        Serialize the course tree recursively, return a flattened list of XBlocks.

        Note that this list will not include detached blocks, those are handled
        in get_detached_xblocks. This method preserves the course ordering for
        non-detached blocks.
        """
        items = [
            self.serialize_xblock(
                parent_block,
                detached_xblock_types,
                initial["dump_id"],
                initial["time_last_dumped"],
            )
        ]

        for child in parent_block.get_children():
            items.extend(
                self.get_xblocks_recursive(child, detached_xblock_types, initial)
            )

        return items

    def get_detached_xblocks(self, course_blocks, detached_xblock_types, initial):
        """
        Spin through the flat list of all blocks in a course and return only
        the detached blocks. Ordering of non-detached blocks is already
        guaranteed in get_xblocks_recursive. Order of detached blocks
        is not guaranteed.
        """
        return [
            self.serialize_xblock(
                block,
                detached_xblock_types,
                initial["dump_id"],
                initial["time_last_dumped"],
            )
            for block in course_blocks
            if block.scope_ids.block_type in detached_xblock_types
        ]

    def serialize_item(self, item, many=False, initial=None):
        """
        Serialize an XBlock into a dict
        """
        course_key = CourseKey.from_string(item["course_key"])
        modulestore = get_modulestore()
        detached_xblock_types = get_detached_xblock_types()

        location_to_node = {}

        # This call gets the entire course tree in order, because the
        # get_items call does not guarantee ordering. It does not return
        # detached blocks, so we gather them separately below.
        course_block = modulestore.get_course(
            course_key, revision=MODULESTORE_PUBLISHED_ONLY_FLAG
        )

        items = self.get_xblocks_recursive(course_block, detached_xblock_types, initial)

        # Here we fetch the detached blocks and add them to the list.
        detached = self.get_detached_xblocks(
            modulestore.get_items(course_key, revision=MODULESTORE_PUBLISHED_ONLY_FLAG),
            detached_xblock_types,
            initial,
        )

        items.extend(detached)

        # Add location and tag data to the dict mappings of the blocks
        index = 0
        section_idx = 0
        subsection_idx = 0
        unit_idx = 0

        for block in items:
            index += 1

            block["order"] = index

            # Ensure that detached types aren't part of the tree
            if block["xblock_data_json"]["detached"]:
                block["xblock_data_json"]["section"] = 0
                block["xblock_data_json"]["subsection"] = 0
                block["xblock_data_json"]["unit"] = 0
            else:
                if block["xblock_data_json"]["block_type"] == "chapter":
                    section_idx += 1
                    subsection_idx = 0
                    unit_idx = 0
                elif block["xblock_data_json"]["block_type"] == "sequential":
                    subsection_idx += 1
                    unit_idx = 0
                elif block["xblock_data_json"]["block_type"] == "vertical":
                    unit_idx += 1

                block["xblock_data_json"]["section"] = section_idx
                block["xblock_data_json"]["subsection"] = subsection_idx
                block["xblock_data_json"]["unit"] = unit_idx

            block["xblock_data_json"]["tags"] = get_tags_for_block(
                block["location"],
            )

            block["xblock_data_json"] = json.dumps(block["xblock_data_json"])
            location_to_node[block["location"]] = block

        return list(location_to_node.values())

    def serialize_xblock(self, item, detached_xblock_types, dump_id, time_last_dumped):
        """Serialize an XBlock instance into a dict"""
        course_key = item.scope_ids.usage_id.course_key
        block_type = item.scope_ids.block_type

        # Extra data not needed for the table to function, things can be
        # added here without needing to rebuild the whole table.
        json_data = {
            "course": course_key.course,
            "run": course_key.run,
            "block_type": block_type,
            "detached": 1 if block_type in detached_xblock_types else 0,
            "graded": 1 if getattr(item, "graded", False) else 0,
            "completion_mode": getattr(item, "completion_mode", ""),
        }

        # Core table data, if things change here it's a big deal.
        serialized_block = {
            "org": course_key.org,
            "course_key": str(course_key),
            "location": str(XBlockSink.strip_branch_and_version(item.location)),
            "display_name": item.display_name_with_default.replace("'", "'"),
            "xblock_data_json": json_data,
            # We need to add this here so the key will be in the right place
            # in the generated csv
            "order": -1,
            "edited_on": str(getattr(item, "edited_on", "")),
            "dump_id": dump_id,
            "time_last_dumped": time_last_dumped,
        }

        return serialized_block

    @staticmethod
    def strip_branch_and_version(location):
        """
        Removes the branch and version information from a location.
        Args:
            location: an xblock's location.
        Returns: that xblock's location without branch and version information.
        """
        return location.for_branch(None)


class CourseOverviewSink(ModelBaseSink):  # pylint: disable=abstract-method
    """
    Sink for CourseOverview model
    """

    model = "course_overviews"
    unique_key = "course_key"
    clickhouse_table_name = "course_overviews"
    timestamp_field = "time_last_dumped"
    name = "Course Overview"
    serializer_class = CourseOverviewSerializer
    nested_sinks = [XBlockSink]
    pk_format = str

    def should_dump_item(self, item):
        """
        Only dump the course if it's been changed since the last time it's been
        dumped.
        Args:
            course_key: a CourseKey object.
        Returns:
            - whether this course should be dumped (bool)
            - reason why course needs, or does not need, to be dumped (string)
        """

        course_last_dump_time = self.get_last_dumped_timestamp(item)

        # If we don't have a record of the last time this command was run,
        # we should serialize the course and dump it
        if course_last_dump_time is None:
            return True, "Course is not present in ClickHouse"

        course_last_published_date = self.get_course_last_published(item)

        # If we've somehow dumped this course but there is no publish date
        # skip it
        if course_last_dump_time and course_last_published_date is None:
            return False, "No last modified date in CourseOverview"

        # Otherwise, dump it if it is newer
        course_last_dump_time = datetime.datetime.strptime(
            course_last_dump_time, "%Y-%m-%d %H:%M:%S.%f+00:00"
        )
        course_last_published_date = datetime.datetime.strptime(
            course_last_published_date, "%Y-%m-%d %H:%M:%S.%f+00:00"
        )
        needs_dump = course_last_dump_time < course_last_published_date

        if needs_dump:
            reason = (
                "Course has been published since last dump time - "
                f"last dumped {course_last_dump_time} < last published {str(course_last_published_date)}"
            )
        else:
            reason = (
                f"Course has NOT been published since last dump time - "
                f"last dumped {course_last_dump_time} >= last published {str(course_last_published_date)}"
            )
        return needs_dump, reason

    def get_course_last_published(self, course_overview):
        """
        Get approximate last publish date for the given course.
        We use the 'modified' column in the CourseOverview table as a quick and easy
        (although perhaps inexact) way of determining when a course was last
        published. This works because CourseOverview rows are re-written upon
        course publish.
        Args:
            course_key: a CourseKey
        Returns: The datetime the course was last published at, stringified.
            Uses Python's default str(...) implementation for datetimes, which
            is sortable and similar to ISO 8601:
            https://docs.python.org/3/library/datetime.html#datetime.date.__str__
        """
        approx_last_published = course_overview.modified
        if approx_last_published:
            return str(approx_last_published)

        return None
