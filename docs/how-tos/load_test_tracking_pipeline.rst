.. _load-test-tracking-event-pipelines:

Load Testing Tracking Event Pipelines
#####################################

Aspects has several ways of getting learning traces from tracking events to xAPI statements and then to ClickHouse. In order to be able to emulate them all in a realistic way for performance testing we've created two management commands that are available in edx-platform when ``platform-plugin-aspects`` is installed:

``load_test_tracking_events`` generates tracking events by creating a test course, a configured number of test users, and enrolling / unenrolling them in a loop. There are options to run a fixed number of events, or to run until killed. There is also a configurable sleep time that can be calibrated for long soak tests, or set to 0 to run in a tight loop. `Note: This needs to be run in CMS as it uses CMS APIs to create the course!`

All options and defaults are described by running:

``tutor local run cms ./manage.py cms load_test_tracking_events --help``


``monitor_load_test_tracking`` gathers performance data on the given system while a test is running and stores the data in ClickHouse for later reporting. A configurable sleep time allows you to determine how often stats are collected. The supported backends are:

- ``celery``
- ``vector``
- ``redis_bus``
- ``kafka_bus``

All options and defaults are described by running:

``tutor local run lms ./manage.py lms monitor_load_test_tracking --help``

Each backend stores different statistics, since they each have unique properties. They log the most important stats to the the console for easy monitoring of the test. The data points we're most interested in capturing are:

- How old is the most recent xAPI event in ClickHouse? What is the lag from event generation to being queryable?
- How far behind is the pipeline? How many events per second can this configuration handle? When will we run out of storage and break the system?


Running a test
--------------

**The test will create persistent data in your environment and may overwhelm your LMS! Do not run on production server!**

#. Make sure you have an isolated test system that is configured in a way that you understand. The point of the test is to stress the system, so using shared infrastructure will skew the test results or potentially cause outages.

#. Note which backend your system is configured to use, by default Open edX uses Celery.

#. Make sure this plugin is installed and activated, configuration has been saved, and you have rebuilt the ``openedx`` image.

#. Start up your environment and let it hit steady state, you may wish to log in and go to the course homepage just to make sure all startup is complete, otherwise the first events will be artificially slow.

#. Start the monitor. This command will pull ClickHouse lag and Celery queue lengths every 5 seconds: ``tutor local run lms ./manage.py lms monitor_load_test_tracking --backend celery --sleep_time 5``

#. Start the test. This command will create a test course, 10 test users, and create 100 events with 0.5 seconds sleep in between: ``tutor local run cms ./manage.py cms load_test_tracking_events --num_users 10 --num_events 100 --sleep_time 0.5``

#. Alternatively you can run a test that will continue until stopped, and configure a prefix to your user names if you want to separate them from other tests in the database: ``tutor local run cms ./manage.py cms load_test_tracking_events --num_users 10 --run_until_killed --sleep_time 0.5 --username_prefix loadtest2_``

#. Runs can be tagged with any number of tags that may help identify and compare different runs. For instance ``--tags celery 10k batch10 2workers``

#. You can stop the test and monitor with ``ctrl-c``, but the monitor will automatically stop once it detects that the run has ended and the queue of events has been drained from the backend.

#. Check the table in ClickHouse for the results of the run: ``event_sink.load_test_stats`` and ``event_sink.load_test_runs``. Each run has a unique identifier, and each row has a timestamp. The stats themselves are stored in JSON as they differ a great deal between backends. With this information you should be able to chart a run and see how the system performs at various levels of load.

Reporting on Tests
------------------

We are currently using the following query to report on the various runs. Note that it is currently hard coded to a 5 second sleep time on the monitor script, but can be updated to use the time between rows instead::

    with starts as (
        select run_id, timestamp, stats, runs.extra,
                row_number() over (
                    partition by run_id order by timestamp
                ) as rn
        from event_sink.load_test_stats stats
        inner join event_sink.load_test_runs runs
            on stats.run_id = runs.run_id
            and runs.event_type = 'start'
    )

    select run_id,
        timestamp,
        starts.timestamp as start_time,
        JSONExtractKeys(stats)[2] as backend,
        multiIf(
            backend = 'celery', JSON_VALUE(stats, '$.celery.lag'),
            backend = 'vector', JSON_VALUE(stats, '$.vector.lag'),
            backend = 'redis_bus', JSON_VALUE(stats, '$.redis_bus.lag'),
            backend = 'kafka_bus', JSON_VALUE(stats, '$.kafka_bus.lag'),
            ''
        ) as service_lag_1,
        if(service_lag_1 = '', '0', service_lag_1) as service_lag,
        JSON_VALUE(stats, '$.clickhouse.lag_seconds') as clickhouse_lag,
        JSON_VALUE(stats, '$.clickhouse.total_rows')::Int - JSON_VALUE(starts.stats, '$.clickhouse.total_rows')::Int as clickhouse_rows,

        lagInFrame(clickhouse_rows, 1) over (PARTITION BY run_id, tags ORDER BY timestamp) as last_rows,
        (clickhouse_rows - last_rows) / 5 as rps,

        ceiling(dateDiff('second', starts.timestamp, timestamp)/5.0) * 5 as secs_into_test,
        trim(BOTH '"' FROM arrayJoin(JSONExtractArrayRaw(starts.extra, 'tags'))) tags,
        backend || ' (' || run_id || ', '|| start_time::String || ')' as name
    from event_sink.load_test_stats stats
    inner join starts on stats.run_id = starts.run_id
    where starts.rn = 1;


Celery Notes
------------

Celery can be scaled by adding more CMS workers and changing the `batch sizes`_.

The JSON in ClickHouse for Celery looks like this::

    {
        "clickhouse": {
            "total_rows": "1273",  # Total xAPI rows in the database
            "most_recent_event": "2024-03-12 14:46:32.828206",
            "lag_seconds": "2912"  # Difference between now() and the most_recent_event
        },
        "celery": {
            "lms_queue_length": 0,  # Size of the redis queue of pending Celery tasks for the LMS workers
            "cms_queue_length": 0,  # Size of the redis queue of pending Celery tasks for the CMS workers
            "lag": 0                # Total of LMS and CMS queue lengths
        }
    }


Vector Notes
------------

Vector scales differently depending on your deployment strategy. Note that Vector's stats are different from other backends. We are only able to calculate the lag between when Vector reads a line from the logs and when it is sent to ClickHouse. There is no way of telling how far behind the log Vector is, but this lag is still useful to see if ClickHouse insert times are slowing down Vector. Instead we should rely on the ClickHouse lag_seconds metric to get a better idea of how far behind Vector is.

Event-routing-backends batch settings don't generally impact Vector. Vector will automatically perform batch inserts to ClickHouse. See the Vector `ClickHouse sink docs`_ for relevant settings to tweak.

The JSON in ClickHouse for Vector looks like this::

    {
        "clickhouse": {
            "total_rows": "1273",  # Total xAPI rows in the database
            "most_recent_event": "2024-03-12 14:46:32.828206",
            "lag_seconds": "2912"  # Difference between now() and the most_recent_event
        },
        "vector": {
            "events_received": 20.0,
            "events_sent": 10.0,
            "lag": 10.0
            }
        }
    }



Redis Bus Notes
---------------

The redis bus can be scaled by adding more consumers or adjusting the `batch sizes`_.

The JSON in ClickHouse for redis bus looks like this::

    {
        "clickhouse": {
            "total_rows": "1273",  # Total xAPI rows in the database
            "most_recent_event": "2024-03-12 14:46:32.828206",
            "lag_seconds": "2912"  # Difference between now() and the most_recent_event
        },
        "redis_bus": {
            "total_events": 77,  # Total number of events that have been added to the redis Stream
            "lag": 10            # Number of events waiting in the stream to be handled
        }
    }


Kafka Bus Notes
---------------

The Kafka bus can be scaled by adding more consumers.

The JSON in ClickHouse for the Kafka bus looks like this::

    {
        "clickhouse": {
            "total_rows": "1273",  # Total xAPI rows in the database
            "most_recent_event": "2024-03-12 14:46:32.828206",
            "lag_seconds": "2912"  # Difference between now() and the most_recent_event
        },
        "kafka_bus": {
            "topic": "dev-analytics",  # The name of the Kafka topic that's being read
            "partitions": [
                {
                    "partition": 0,  # The index of the partition
                    "lag": 150       # How many events are waiting to be processed by the partition
                }
            ],
            "lag": 150               # Total waiting events across all partitions
        }
    }


.. _batch sizes: https://event-routing-backends.readthedocs.io/en/latest/getting_started.html?#batching-configuration
.. _ClickHouse sink docs: https://vector.dev/docs/reference/configuration/sinks/clickhouse/
