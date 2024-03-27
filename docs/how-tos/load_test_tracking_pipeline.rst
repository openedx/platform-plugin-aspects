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

**The test will create persistent data in your environment! Do not run on production server!**

#. Make sure you have an isolated test system that is configured in a way that you understand. The point of the test is to stress the system, so using shared infrastructure will skew the test results or potentially cause outages.

#. Note which backend your system is configured to use, by default Open edX uses Celery.

#. Make sure this plugin is installed and activated, configuration has been saved, and you have rebuilt the ``openedx`` image.

#. Start up your environment and let it hit steady state, you may wish to log in and go to the course homepage just to make sure all startup is complete, otherwise the first events will be artificially slow.

#. Start the monitor. This command will pull ClickHouse lag and Celery queue lengths every 5 seconds: ``tutor local run lms ./manage.py lms monitor_load_test_tracking --backend celery --sleep_time 5``

#. Start the test. This command will create a test course, 10 test users, and create 100 events with 0.5 seconds sleep in between: ``tutor local run cms ./manage.py cms load_test_tracking_events --num_users 10 --num_events 100 --sleep_time 0.5``

#. Alternatively you can run a test that will continue until stopped, and configure a prefix to your user names if you want to separate them from other tests in the database: ``tutor local run cms ./manage.py cms load_test_tracking_events --num_users 10 --run_until_killed --sleep_time 0.5 --username_prefix loadtest2_``

#. Stop the test and monitor with ``ctrl-c``, you may want to let the monitor run until the queue of your system is cleared to get full data on how long it takes to recover from a backlog of events.

#. Check the table in ClickHouse for the results of the run: ``event_sink.load_test_stats``. Each run has a unique identifier, and each row has a timestamp. The stats themselves are stored in JSON as they differ a great deal between backends. With this information you should be able to chart a run and see how the system performs at various levels of load.

Celery Notes
------------

Celery can be scaled by adding more CMS workers.

The JSON in ClickHouse for Celery looks like this::

    {
        "clickhouse": {
            "total_rows": "1273",  # Total xAPI rows in the database
            "most_recent_event": "2024-03-12 14:46:32.828206",
            "lag_seconds": "2912"  # Difference between now() and the most_recent_event
        },
        "celery": {
            "lms_queue_length": 0,  # Size of the redis queue of pending Celery tasks for the LMS workers
            "cms_queue_length": 0   # Size of the redis queue of pending Celery tasks for the CMS workers
        }
    }


Vector Notes
------------

Vector scales differently depending on your deployment strategy. Note that Vector's stats are different from other backends. We are only able to calculate the lag between when Vector reads a line from the logs and when it is sent to ClickHouse. There is no way of telling how far behind the log Vector is, but this lag is still useful to see if ClickHouse insert times are slowing down Vector. Instead we should rely on the ClickHouse lag_seconds metric to get a better idea of how far behind Vector is.

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

The redis bus can be scaled by adding more consumers.

The JSON in ClickHouse for redis bus looks like this::

    {
        "clickhouse": {
            "total_rows": "1273",  # Total xAPI rows in the database
            "most_recent_event": "2024-03-12 14:46:32.828206",
            "lag_seconds": "2912"  # Difference between now() and the most_recent_event
        },
        "redis_bus": {
            "total_events": 77,  # Total number of events that have been added to the redis Stream
            "consumers": [
                {
                    "name": "aspects",  # Name of each consumer in the consumer group
                    "processing": 0,       # How many events are currently being processed by that consumer (should be 0 or 1)
                    "queue_length": 0      # How many events are waiting to be processed in the stream
                }
            ]
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
            ]
        }
    }

