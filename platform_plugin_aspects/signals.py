"""
Signal handler functions, mapped to specific signals in apps.py.
"""

from django.db import transaction
from django.db.models.signals import post_save
from django.dispatch import Signal, receiver

from platform_plugin_aspects.sinks import (
    CourseEnrollmentSink,
    ExternalIdSink,
    UserProfileSink,
    UserRetirementSink,
)
from platform_plugin_aspects.utils import get_model

try:
    from openedx.core.djangoapps.user_api.accounts.signals import USER_RETIRE_LMS_MISC
except ImportError:
    # Tests don't have the platform installed
    USER_RETIRE_LMS_MISC = Signal()


def receive_course_publish(  # pylint: disable=unused-argument  # pragma: no cover
    sender, course_key, **kwargs
):
    """
    Receives COURSE_PUBLISHED signal and queues the dump job.
    """
    # import here, because signal is registered at startup, but items in tasks are not yet able to be loaded
    from platform_plugin_aspects.tasks import (  # pylint: disable=import-outside-toplevel
        dump_course_to_clickhouse,
    )

    dump_course_to_clickhouse.delay(str(course_key))


def receive_course_enrollment_changed(  # pylint: disable=unused-argument  # pragma: no cover
    sender, **kwargs
):
    """
    Receives ENROLL_STATUS_CHANGE signal and queues the dump job.
    """
    from platform_plugin_aspects.tasks import (  # pylint: disable=import-outside-toplevel
        dump_data_to_clickhouse,
    )

    user = kwargs.get("user")
    course_id = kwargs.get("course_id")

    CourseEnrollment = get_model("course_enrollment")
    instance = CourseEnrollment.objects.get(user=user, course_id=course_id)

    sink = CourseEnrollmentSink(None, None)

    dump_data_to_clickhouse.delay(
        sink_module=sink.__module__,
        sink_name=sink.__class__.__name__,
        object_id=instance.id,
    )


def on_user_profile_updated(instance):
    """
    Queues the UserProfile dump job when the parent transaction is committed.
    """
    # import here, because signal is registered at startup, but items in tasks are not yet able to be loaded
    from platform_plugin_aspects.tasks import (  # pylint: disable=import-outside-toplevel
        dump_data_to_clickhouse,
    )

    sink = UserProfileSink(None, None)
    dump_data_to_clickhouse.delay(
        sink_module=sink.__module__,
        sink_name=sink.__class__.__name__,
        object_id=str(instance.id),
    )


def on_user_profile_updated_txn(**kwargs):
    """
    Handle user_profile saves in the middle of a transaction.

    If this gets fired before the transaction commits, the task may try to
    query an id that doesn't exist yet and throw an error. This should postpone
    queuing the Celery task until after the transaction is committed.
    """
    transaction.on_commit(
        lambda: on_user_profile_updated(kwargs["instance"])
    )  # pragma: no cover


# Connect the UserProfile.post_save signal handler only if we have a model to attach to.
# (prevents celery errors during tests)
_user_profile = get_model("user_profile")
if _user_profile:
    post_save.connect(
        on_user_profile_updated_txn, sender=_user_profile
    )  # pragma: no cover


def on_externalid_saved(  # pylint: disable=unused-argument  # pragma: no cover
    sender, instance, **kwargs
):
    """
    Receives post save signal and queues the dump job.
    """
    # import here, because signal is registered at startup, but items in tasks are not yet able to be loaded
    from platform_plugin_aspects.tasks import (  # pylint: disable=import-outside-toplevel
        dump_data_to_clickhouse,
    )

    sink = ExternalIdSink(None, None)
    dump_data_to_clickhouse.delay(
        sink_module=sink.__module__,
        sink_name=sink.__class__.__name__,
        object_id=str(instance.id),
    )


# Connect the ExternalId.post_save signal handler only if we have a model to attach to.
# (prevents celery errors during tests)
_external_id = get_model("external_id")
if _external_id:
    post_save.connect(on_externalid_saved, sender=_external_id)  # pragma: no cover


@receiver(USER_RETIRE_LMS_MISC)
def on_user_retirement(  # pylint: disable=unused-argument  # pragma: no cover
    sender, user, **kwargs
):
    """
    Receives a user retirement signal and queues the retire_user job.
    """
    # import here, because signal is registered at startup, but items in tasks are not yet able to be loaded
    from platform_plugin_aspects.tasks import (  # pylint: disable=import-outside-toplevel
        dump_data_to_clickhouse,
    )

    sink = UserRetirementSink(None, None)
    dump_data_to_clickhouse.delay(
        sink_module=sink.__module__,
        sink_name=sink.__class__.__name__,
        object_id=str(user.id),
    )
