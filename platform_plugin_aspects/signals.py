"""
Signal handler functions, mapped to specific signals in apps.py.
"""

from django.db import transaction
from django.db.models.signals import post_delete, post_save
from django.dispatch import Signal, receiver
from opaque_keys import InvalidKeyError

from platform_plugin_aspects.sinks import (
    CourseEnrollmentSink,
    ExternalIdSink,
    ObjectTagSink,
    TagSink,
    TaxonomySink,
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


def on_user_profile_updated_txn(*args, **kwargs):
    """
    Handle user_profile saves in the middle of a transaction.

    Handle saves in the middle of a transaction.
    If this gets fired before the transaction commits, the task may try to
    query an id that doesn't exist yet and throw an error. This should postpone
    queuing the Celery task until after the transaction is committed.
    """

    def on_user_profile_updated(instance, **kwargs):
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

    transaction.on_commit(lambda: on_user_profile_updated(*args, **kwargs))


# Connect the UserProfile.post_save signal handler only if we have a model to attach to.
# (prevents celery errors during tests)
_user_profile = get_model("user_profile")
if _user_profile:
    post_save.connect(
        on_user_profile_updated_txn, sender=_user_profile
    )  # pragma: no cover


def on_externalid_saved_txn(*args, **kwargs):
    """
    Handle external_id saves in the middle of a transaction.

    Handle saves in the middle of a transaction.
    If this gets fired before the transaction commits, the task may try to
    query an id that doesn't exist yet and throw an error. This should postpone
    queuing the Celery task until after the transaction is committed.
    """

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

    transaction.on_commit(lambda: on_externalid_saved(*args, **kwargs))


# Connect the ExternalId.post_save signal handler only if we have a model to attach to.
# (prevents celery errors during tests)
_external_id = get_model("external_id")
if _external_id:
    post_save.connect(on_externalid_saved_txn, sender=_external_id)  # pragma: no cover


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


def on_tag_saved_txn(*args, **kwargs):
    """
    Handle external_id saves in the middle of a transaction.

    Handle saves in the middle of a transaction.
    If this gets fired before the transaction commits, the task may try to
    query an id that doesn't exist yet and throw an error. This should postpone
    queuing the Celery task until after the transaction is committed.
    """

    def on_tag_saved(  # pylint: disable=unused-argument  # pragma: no cover
        sender, instance, **kwargs
    ):
        """
        Receives post save signal and queues the dump job.
        """
        # import here, because signal is registered at startup, but items in tasks are not yet able to be loaded
        from platform_plugin_aspects.tasks import (  # pylint: disable=import-outside-toplevel
            dump_data_to_clickhouse,
        )

        sink = TagSink(None, None)
        dump_data_to_clickhouse.delay(
            sink_module=sink.__module__,
            sink_name=sink.__class__.__name__,
            object_id=str(instance.id),
        )

    transaction.on_commit(lambda: on_tag_saved(*args, **kwargs))


# Connect the ExternalId.post_save signal handler only if we have a model to attach to.
# (prevents celery errors during tests)
_tag = get_model("tag")
if _tag:
    post_save.connect(on_tag_saved_txn, sender=_tag)  # pragma: no cover


def on_taxonomy_saved_txn(*args, **kwargs):
    """
    Handle external_id saves in the middle of a transaction.

    Handle saves in the middle of a transaction.
    If this gets fired before the transaction commits, the task may try to
    query an id that doesn't exist yet and throw an error. This should postpone
    queuing the Celery task until after the transaction is committed.
    """

    def on_taxonomy_saved(  # pylint: disable=unused-argument  # pragma: no cover
        sender, instance, **kwargs
    ):
        """
        Receives post save signal and queues the dump job.
        """
        # import here, because signal is registered at startup, but items in tasks are not yet able to be loaded
        from platform_plugin_aspects.tasks import (  # pylint: disable=import-outside-toplevel
            dump_data_to_clickhouse,
        )

        sink = TaxonomySink(None, None)
        dump_data_to_clickhouse.delay(
            sink_module=sink.__module__,
            sink_name=sink.__class__.__name__,
            object_id=str(instance.id),
        )

    transaction.on_commit(lambda: on_taxonomy_saved(*args, **kwargs))


# Connect the ExternalId.post_save signal handler only if we have a model to attach to.
# (prevents celery errors during tests)
_taxonomy = get_model("taxonomy")
if _taxonomy:
    post_save.connect(on_taxonomy_saved_txn, sender=_taxonomy)  # pragma: no cover


def on_object_tag_saved_txn(*args, **kwargs):
    """
    Handle external_id saves in the middle of a transaction.

    Handle saves in the middle of a transaction.
    If this gets fired before the transaction commits, the task may try to
    query an id that doesn't exist yet and throw an error. This should postpone
    queuing the Celery task until after the transaction is committed.
    """

    def on_object_tag_saved(sender, instance, **kwargs):  # pragma: no cover
        """
        Receives post save signal and queues the dump job.
        """
        # import here, because signal is registered at startup, but items in tasks are not yet able to be loaded
        from platform_plugin_aspects.tasks import (  # pylint: disable=import-outside-toplevel
            dump_data_to_clickhouse,
        )

        sink = ObjectTagSink(None, None)
        dump_data_to_clickhouse.delay(
            sink_module=sink.__module__,
            sink_name=sink.__class__.__name__,
            object_id=str(instance.id),
        )

        on_object_tag_deleted(sender, instance, **kwargs)

    transaction.on_commit(lambda: on_object_tag_saved(*args, **kwargs))


def on_object_tag_deleted(  # pylint: disable=unused-argument  # pragma: no cover
    sender, instance, **kwargs
):
    """
    Receives post save signal and queues the dump job.
    """
    # import here, because signal is registered at startup, but items in tasks are not yet able to be loaded
    from platform_plugin_aspects.tasks import (  # pylint: disable=import-outside-toplevel
        dump_course_to_clickhouse,
    )

    CourseOverview = get_model("course_overviews")
    if CourseOverview:
        try:
            CourseOverview.objects.get(id=instance.object_id)
            dump_course_to_clickhouse.delay(instance.object_id)
        except (CourseOverview.DoesNotExist, InvalidKeyError):
            pass


# Connect the ExternalId.post_save signal handler only if we have a model to attach to.
# (prevents celery errors during tests)
_object_tag = get_model("object_tag")
if _object_tag:  # pragma: no cover
    post_save.connect(on_object_tag_saved_txn, sender=_object_tag)
    post_delete.connect(on_object_tag_deleted, sender=_object_tag)
