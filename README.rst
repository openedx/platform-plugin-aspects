Platform Plugin Aspects
#######################

Purpose
*******

This repository holds various Aspects plugins for the Open edX platform, including the
event sinks that move data from the LMS to ClickHouse and the embedding of Superset
dashboards back into the platform.

Version Compatibility
*********************

- ``platform-plugin-aspects`` version 1.x: Nutmeg to Sumac
- ``platform-plugin-aspects`` version 2.x: Redwood (with in-context metrics turned off), or Sumac and above

Sinks
*****

Sinks are components that listen for events and store them in ClickHouse. The
events are emitted by the Open edX platform via `Open edX events`_ or Django signals.

Available Sinks
===============

Below are the existing sink names and their corresponding object names (as needed for the
``dump_data_to_clickhouse`` command below.

- ``CourseOverviewSink`` - Listens for the ``COURSE_PUBLISHED`` event and stores the
  course structure, including ordering data through ``XBlockSink`` in ClickHouse. Object name:
  ``course_overviews``
- ``ExternalIdSink`` - Listens for the ``post_save`` Django signal on the ``ExternalId``
  model and stores the external id data in ClickHouse. This model stores the relationships
  between users and their xAPI unique identifiers. Object name: ``external_id``
- ``UserProfile`` - Listens for the ``post_save`` Django signal on the ``UserProfile``
  model and stores the user profile data in ClickHouse. Object name: ``user_profile``
- ``CourseEnrollmentSink`` - Listen for the ``ENROLL_STATUS_CHANGE`` event and stores
  the course enrollment data. Object name: ``course_enrollment``
- ``UserRetirementSink`` - Listen for the ``USER_RETIRE_LMS_MISC`` Django signal and
  remove the user PII information from ClickHouse. This is a special sink with no assigned object name.

Commands
========

In addition to being an event listener, this package provides the following commands:

- ``dump_data_to_clickhouse`` - This command allows bulk export of the data from the Sinks.
  Allows bootstrapping a new data platform or backfilling lost or missing data. Each sink object
  is dumped individually. For large dumps, you can use the ``--batch_size`` and ``--sleep_time`` to control
  how much load is placed on your LMS / Studio servers. Examples:

  Dump any courses that the system thinks are out of date (last publish time is newer than the
  last dump time in ClickHouse):

  .. code-block:: bash

    python manage.py cms dump_data_to_clickhouse --object course_overviews

  The ``force`` option will dump all objects, regardless of the data ClickHouse currently has
  so this command will push all course data for all courses:

  .. code-block:: bash

    python manage.py cms dump_data_to_clickhouse --object course_overviews --force

  These commands will dump the user data Aspects uses when PII is turned on:

  .. code-block:: bash

    python manage.py cms dump_data_to_clickhouse --object external_id
    python manage.py cms dump_data_to_clickhouse --object user_profile

  To reduce server load, this command will dump 1000 user profiles at a time, with a 5-second
  sleep in between:

  .. code-block:: bash

    python manage.py cms dump_data_to_clickhouse --object user_profile --batch_size 1000 --sleep_time 5

  There are many more options that can be used for different circumstances. Please refer to
  the commands help for more information. There is also a Tutor command that wraps this, so
  that you don't need to get shell on a container to execute this command. More information on
  that can be found in the `Aspects backfill documentation`_.

- ``load_test_tracking_events`` - This command allows loading test tracking events into
  ClickHouse. This is useful for testing the ClickHouse connection to measure the performance of the
  different data pipelines, such as Vector, Event Bus (Redis and Kafka), and Celery.

  **Do not use this command in production**, as it will generate a large amount of data
  and will slow down the system.

  .. code-block:: bash

    python manage.py cms load_test_tracking_events

- ``monitor_load_test_tracking`` - Monitors the load test tracking script and saves
  output for later analysis.

  .. code-block:: bash

    python manage.py cms monitor_load_test_tracking

Instructor Dashboard Integration
================================

Dashboards from `Aspects`_ are integrated into the Instructor Dashboard via `Superset Embedded SDK`_.
See `Configuration`_ for more details.

Getting Started with Development
********************************

Please see the Open edX documentation for `guidance on Python development <https://docs.openedx.org/en/latest/developers/how-tos/get-ready-for-python-dev.html>`_ in this repo.

Deploying
*********

The ``Platform Plugin Aspects`` component is a django plugin that doesn't
need independent deployment. Therefore, its setup is reasonably straightforward.
First, it needs to be added to your service requirements, and then it will be
installed alongside the requirements of the service.

Configuration
*************

Instructor Dashboard Configuration
==================================

The Instructor Dashboard integration uses the `Open edX Filters`_. To learn more about
the filters, see the `Open edX Filters`_ documentation. Make sure to configure the
superset pipeline into the filter as follows:

.. code-block:: python

  OPEN_EDX_FILTERS_CONFIG = {
    "org.openedx.learning.instructor.dashboard.render.started.v1": {
      "fail_silently": False,
      "pipeline": [
        "platform_plugin_superset.extensions.filters.AddSupersetTab",
      ]
    },
  }

- ``SUPERSET_CONFIG`` - This setting is used to configure the Superset Embedded SDK.
  The configuration is a dictionary that contains the following keys:

  - ``internal_service_url`` - The URL of the Superset instance (useful in development, omit in production).
  - ``service_url`` - The URL of the Superset instance.
  - ``username`` - The username of the Superset user.
  - ``password`` - The password of the Superset user.

- ``ASPECTS_INSTRUCTOR_DASHBOARDS`` - This setting is used to configure the dashboards
  that will be displayed in the Instructor Dashboard. The configuration is a list of
  dictionaries that contains the following keys:

  - ``name`` - The name of the dashboard.
  - ``slug`` - The slug of the dashboard.
  - ``uuid`` - The UUID of the dashboard.
  - ``allow_translations`` - A boolean value that determines if the dashboard is translated in `Aspects`_.

- ``SUPERSET_EXTRA_FILTERS_FORMAT`` - This setting is used to configure the extra filters
  that will be applied to the dashboards. The configuration is a list of strings that
  can be formatted with the following variables:

  - ``user`` - The user object.
  - ``course`` - The course object.

- ``SUPERSET_DASHBOARD_LOCALES`` - This setting is used to configure the available locales
  for the dashboards. The configuration is a list of supported locales by `Aspects`_.

- ``ASPECTS_ENABLE_STUDIO_IN_CONTEXT_METRICS`` - This setting turns on and off the in-context
  metrics feature. It must be turned off in Open edX releases before Sumac, and when using
  ``tutor-contrib-aspects`` before v2.2.0, as those dashboards will not exist, causing errors in
  the embedded Instructor Dashboards.

- ``ASPECTS_IN_CONTEXT_DASHBOARDS`` - This setting mirrors the ``ASPECTS_INSTRUCTOR_DASHBOARDS``, but
  with additional keys used for filtering the boards to specific courses and blocks.

Event Sink Configuration
========================

- ``EVENT_SINK_CLICKHOUSE_BACKEND_CONFIG`` - This setting is used to configure the ClickHouse
  connection. The configuration is a dictionary that contains the following keys:

  - ``url`` - The host of the ClickHouse instance.
  - ``database`` - The database name.
  - ``username`` - The username of the ClickHouse user.
  - ``password`` - The password of the ClickHouse user.
  - ``timeout_secs`` - The timeout in seconds for the ClickHouse connection.

- ``EVENT_SINK_CLICKHOUSE_PII_MODELS`` - This setting is used to configure the models that
  contain PII information. The configuration is a list of strings that contain the
  table names where the PII information is stored.

- ``EVENT_SINK_CLICKHOUSE_MODEL_CONFIG`` - This setting is used to provide compatibility
  with multiple Open edX models. The configuration is a dictionary that contains the
  following: a key per model that contains a dictionary with the following keys:

  - ``module`` - The module path of the model.
  - ``model`` - The model class name.

Event Sinks are disabled by default. To enable them, you need to enable the following
waffle flag: ``event_sink_clickhouse.{{model_name}}.enabled``, where model_name is the name
of the model that you want to enable. Or, you can enable them via settings by setting
``EVENT_SINK_CLICKHOUSE_{{model_name}}_ENABLED`` to ``True``.


Getting Help
************

Documentation
=============

Start by going through `the documentation`_.  If you need more help see below.

.. _the documentation: https://docs.openedx.org/projects/platform-plugin-aspects

More Help
=========

If you're having trouble, we have discussion forums at
https://discuss.openedx.org, where you can connect with others in the
community.

Our real-time conversations are on Slack. You can request a `Slack
invitation`_, then join our `community Slack workspace`_.

For anything non-trivial, the best path is to open an issue in this
repository with as many details about the issue you are facing as you
can provide.

https://github.com/openedx/platform-plugin-aspects/issues

For more information about these options, see the `Getting Help <https://openedx.org/getting-help>`__ page.

.. _Slack invitation: https://openedx.org/slack
.. _community Slack workspace: https://openedx.slack.com/

License
*******

Please see `LICENSE.txt <LICENSE.txt>`_ for details.

Contributing
************

Contributions are very welcome.
Please read `How To Contribute <https://openedx.org/r/how-to-contribute>`_ for details.

This project is currently accepting all types of contributions, bug fixes,
security fixes, maintenance work, or new features.  However, please make sure
to have a discussion about your new feature idea with the maintainers prior to
beginning development to maximize the chances of your change being accepted.
You can start a conversation by creating a new issue on this repo summarizing
your idea.

The Open edX Code of Conduct
****************************

All community members are expected to follow the `Open edX Code of Conduct`_.

.. _Open edX Code of Conduct: https://openedx.org/code-of-conduct/

People
******

The assigned maintainers for this component and other project details may be
found in `Backstage`_. Backstage pulls this data from the ``catalog-info.yaml``
file in this repo.

.. _Backstage: https://backstage.openedx.org/catalog/default/component/platform-plugin-aspects

Reporting Security Issues
*************************

Please do not report security issues in public. Please email security@openedx.org.

.. _Open edX events: https://github.com/openedx/openedx-events
.. _Edx Platform: https://github.com/openedx/edx-platform
.. _ClickHouse: https://clickhouse.com
.. _Aspects: https://docs.openedx.org/projects/openedx-aspects/en/latest/index.html
.. _Superset Embedded SDK: https://www.npmjs.com/package/@superset-ui/embedded-sdk
.. _Open edX Filters: https://docs.openedx.org/projects/openedx-filters/en/latest/
.. _Aspects backfill documentation:  https://docs.openedx.org/projects/openedx-aspects/en/latest/technical_documentation/how-tos/backfill.html
