"""
Monitors the load test tracking script and saves output for later analysis.
"""

import csv
import datetime
import io
import json
import logging
from textwrap import dedent
from time import sleep
from typing import Any, Union

import redis
import requests
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from platform_plugin_aspects.sinks.base_sink import ClickHouseAuth

try:
    import confluent_kafka
except ImportError:
    confluent_kafka = None

log = logging.getLogger("tracking_event_loadtest_monitor")


class Monitor:
    """
    Manages the configuration and state of the load test monitor.
    """

    run_id = None

    def __init__(self, sleep_time: float, backend: str):
        self.ch_url = settings.EVENT_SINK_CLICKHOUSE_BACKEND_CONFIG["url"]
        self.ch_auth = ClickHouseAuth(
            settings.EVENT_SINK_CLICKHOUSE_BACKEND_CONFIG["username"],
            settings.EVENT_SINK_CLICKHOUSE_BACKEND_CONFIG["password"],
        )
        self.ch_database = settings.EVENT_SINK_CLICKHOUSE_BACKEND_CONFIG["database"]
        self.ch_xapi_database = settings.EVENT_SINK_CLICKHOUSE_BACKEND_CONFIG.get(
            "xapi_database", "xapi"
        )
        self.ch_xapi_table = settings.EVENT_SINK_CLICKHOUSE_BACKEND_CONFIG.get(
            "xapi_table", "xapi_events_all"
        )
        self.ch_stats_table = settings.EVENT_SINK_CLICKHOUSE_BACKEND_CONFIG.get(
            "stats_table", "load_test_stats"
        )
        self.ch_runs_table = settings.EVENT_SINK_CLICKHOUSE_BACKEND_CONFIG.get(
            "runs_table", "load_test_runs"
        )
        self.ch_timeout_secs = settings.EVENT_SINK_CLICKHOUSE_BACKEND_CONFIG[
            "timeout_secs"
        ]
        self.sleep_time = sleep_time
        self.backend = backend

    def check_for_run_id(self) -> Union[str, None]:
        """
        Return a run id for any unfinished run started in the last minute.
        """
        query = f"""
            SELECT run_id
            FROM {self.ch_runs_table} runs
            WHERE event_type = 'start'
            AND run_id NOT IN (
                SELECT run_id
                FROM {self.ch_runs_table}
                WHERE event_type = 'end'
            )
            AND dateDiff('second', now(), timestamp) <= 60
        """

        response = requests.post(
            url=self.ch_url,
            auth=self.ch_auth,
            params={"database": self.ch_database, "query": query},
            timeout=self.ch_timeout_secs,
        )

        response.raise_for_status()

        # ClickHouse will respond with the ID and a newline or an empty string
        return response.text.strip()

    def wait_for_start(self) -> None:
        """
        Wait for a run to start, tested by checking ClickHouse for new run ids.
        """
        while True:
            self.run_id = self.check_for_run_id()

            if self.run_id:
                log.info(f"Found run id {self.run_id}! Starting monitor.")
                return

            log.info("No run id from the last 60 seconds found...")  # pragma: no cover
            sleep(2)  # pragma: no cover

    def test_has_ended(self) -> bool:
        """
        Return True if the current run has finished.
        """
        query = f"""
            SELECT run_id
            FROM {self.ch_runs_table} runs
            WHERE run_id = '{self.run_id}'
            AND event_type = 'end'
        """

        response = requests.post(
            url=self.ch_url,
            auth=self.ch_auth,
            params={"database": self.ch_database, "query": query},
            timeout=self.ch_timeout_secs,
        )

        response.raise_for_status()

        # ClickHouse will respond with the ID and a newline or an empty string
        return response.text.strip() == self.run_id

    def run(self) -> None:
        """
        Wait for a new test to start, then run the monitor until killed.
        """
        collect_redis_bus = self.backend == "redis_bus"
        collect_celery = self.backend == "celery"
        collect_kafka_bus = self.backend == "kafka_bus"
        collect_vector = self.backend == "vector"

        log.info("Waiting for test to start...")
        self.wait_for_start()

        # Once the test has ended we will wait for the backend to drain the
        # backlog before exiting. This tracks the "in between" state.
        shutting_down = False

        while True:
            start = datetime.datetime.now()
            log.info(f"----------- {start} --------")
            lag = None

            current_stats = {"clickhouse": self.get_clickhouse_stats()}
            lag = -1
            if collect_redis_bus:
                current_stats["redis_bus"] = self.get_redis_bus_stats()
                lag = current_stats["redis_bus"]["lag"]
            elif collect_celery:
                current_stats["celery"] = self.get_celery_stats()
                lag = current_stats["celery"]["lag"]
            elif collect_kafka_bus:
                current_stats["kafka_bus"] = self.get_kafka_bus_stats()
                lag = current_stats["kafka_bus"]["lag"]
            elif collect_vector:
                current_stats["vector"] = self.get_vector_stats()
                lag = current_stats["vector"]["lag"]

            self.store_stats(current_stats)

            if not shutting_down and self.test_has_ended():  # pragma: no cover
                shutting_down = True
                log.info(
                    "----- Test has ended, waiting for events to drain off or force end with CTRL-C"
                )

            if shutting_down and not lag:
                log.info("----- Test has ended, events are drained. Ending monitor!")
                break

            # Try to keep our collection cadence to exactly what was asked
            # otherwise
            check_duration = datetime.datetime.now() - start

            if check_duration.total_seconds() >= self.sleep_time:
                log.warning(
                    f"It took {check_duration} to collect and store stats, this is greater than the sleep time!"
                )

            next_sleep = self.sleep_time - check_duration.total_seconds()
            sleep(next_sleep)

    def store_stats(self, current_stats: dict) -> None:
        """
        Send the results for this iteration to ClickHouse.
        """
        stats = json.dumps(current_stats)

        insert = f"""INSERT INTO {self.ch_stats_table} (run_id, stats) FORMAT CSV"""

        output = io.StringIO()
        writer = csv.writer(output, quoting=csv.QUOTE_NONNUMERIC)
        writer.writerow((self.run_id, stats))

        response = requests.post(
            url=self.ch_url,
            auth=self.ch_auth,
            params={"database": self.ch_database, "query": insert},
            data=output.getvalue().encode("utf-8"),
            timeout=self.ch_timeout_secs,
        )

        response.raise_for_status()

    def get_clickhouse_stats(self):
        """
        Get the current state of ClickHouse for this iteration.
        """
        select = f"""
            SELECT
                count(*) as ttl_count,
                max(emission_time) as most_recent,
                date_diff('second', max(emission_time), now()) as lag_seconds
            FROM {self.ch_xapi_table}
            FINAL
            FORMAT JSON
        """

        response = requests.post(
            url=self.ch_url,
            auth=self.ch_auth,
            params={"database": self.ch_xapi_database, "query": select},
            timeout=self.ch_timeout_secs,
        )

        response.raise_for_status()

        resp = response.json()["data"][0]
        log.info(f"Clickhouse lag seconds: {resp['lag_seconds']}")

        return {
            "total_rows": resp["ttl_count"],
            "most_recent_event": resp["most_recent"],
            "lag_seconds": resp["lag_seconds"],
        }

    def get_celery_stats(self):
        """
        Get the current state of Celery for this iteration.
        """
        r = redis.Redis.from_url(settings.BROKER_URL)
        lms_queue = r.llen("edx.lms.core.default")
        cms_queue = r.llen("edx.cms.core.default")

        log.info(f"Celery queues: LMS {lms_queue}, CMS {cms_queue}")

        return {
            "lms_queue_length": lms_queue,
            "cms_queue_length": cms_queue,
            "lag": lms_queue + cms_queue,
        }

    def get_redis_bus_stats(self):
        """
        Get the current state of redis for this iteration.
        """
        r = redis.Redis.from_url(settings.EVENT_BUS_REDIS_CONNECTION_URL)
        info = r.xinfo_stream("openedx-analytics", full=True)

        lag = 0

        try:
            for g in info["groups"]:
                lag += g["lag"]
        # Older versions of redis don't have "lag".
        except KeyError:  # pragma: no cover
            pass

        consumer_stats = {
            "total_events": info["length"],
            "lag": lag,
        }

        log.info(f"Redis bus queue length: {consumer_stats['lag']}")

        return consumer_stats

    def get_kafka_bus_stats(self):
        """
        Get the current state of ClickHouse for this iteration.
        """
        if not confluent_kafka:  # pragma: no cover
            raise CommandError(
                "Trying to monitor Kafka bus, but confluent_kafka is not installed"
            )

        brokers = settings.EVENT_BUS_KAFKA_BOOTSTRAP_SERVERS
        topic = f"{settings.EVENT_BUS_TOPIC_PREFIX}-analytics"
        group = "analytics-service"

        # This consumer will not join the group, but the group.id is required by
        # committed() to know which group to get offsets for.
        consumer = confluent_kafka.Consumer(
            {"bootstrap.servers": brokers, "group.id": group}
        )

        # Get the topic's partitions
        metadata = consumer.list_topics(topic, timeout=10)

        if metadata.topics[topic].error is not None:  # pragma: no cover
            log.info(metadata.topics[topic].error)

        partitions = [
            confluent_kafka.TopicPartition(topic, p)
            for p in metadata.topics[topic].partitions
        ]
        committed = consumer.committed(partitions, timeout=10)

        consumer_stats = {
            "topic": topic,
            "partitions": [],
        }

        total_lag = 0

        for partition in committed:
            # Get the partitions low and high watermark offsets.
            low, high = consumer.get_watermark_offsets(
                partition, timeout=10, cached=False
            )

            if high < 0:  # pragma: no cover
                lag = 0
            elif partition.offset < 0:  # pragma: no cover
                # No committed offset, show total message count as lag.
                # The actual message count may be lower due to compaction
                # and record deletions.
                lag = high - low
            else:
                lag = high - partition.offset

            log.info(f"{partition.topic} [{partition.partition}] Lag: {lag}")
            total_lag += lag

            consumer_stats["partitions"].append(
                {
                    "partition": partition.partition,
                    "lag": lag,
                }
            )

        consumer.close()
        consumer_stats["lag"] = total_lag
        return consumer_stats

    def _call_vector_graphql(self):
        """
        Make the actual GraphQL call to the Vector API.
        """
        # These values are hard coded in tutor local, K8s changes TBD
        url = "http://vector:8686/graphql"
        query = """
        {
          sinks(filter:{componentId:{equals:"clickhouse_xapi"}}) {
            edges {
              node {
                ...on Sink {
                  componentId,
                  componentType,
                  metrics {
                    receivedEventsTotal {timestamp, receivedEventsTotal},
                    sentEventsTotal {timestamp, sentEventsTotal}
                  }
                }
              }
            }
          }
        }
        """
        r = requests.post(url, json={"query": query}, timeout=10)
        r.raise_for_status()
        return r.json()["data"]["sinks"]["edges"][0]["node"]["metrics"]

    def get_vector_stats(self):
        """
        Get the current state of Vector for this iteration.
        """
        metrics = self._call_vector_graphql()

        # These will be null until events start arriving
        received = (
            metrics["receivedEventsTotal"]["receivedEventsTotal"]
            if metrics["receivedEventsTotal"]
            else 0.0
        )
        sent = (
            metrics["sentEventsTotal"]["sentEventsTotal"]
            if metrics["sentEventsTotal"]
            else 0.0
        )

        rtn = {"events_received": received, "events_sent": sent, "lag": received - sent}

        log.info(
            f"Vector received: {rtn['events_received']} sent: {rtn['events_sent']} lag: {rtn.get('lag')}"
        )
        return rtn


class Command(BaseCommand):
    """
    Dump objects to a ClickHouse instance.

    Example:
    tutor local run lms ./manage.py lms monitor_load_test_tracking --sleep_time 5 --backend redis_bus
    """

    help = dedent(__doc__).strip()

    def add_arguments(self, parser: Any) -> None:
        parser.add_argument(
            "--sleep_time",
            type=float,
            default=10,
            help="Fractional number of seconds to sleep between gathering data.",
        )
        parser.add_argument(
            "--backend",
            choices=["redis_bus", "kafka_bus", "celery", "vector"],
            default="celery",
            help="Backend used to send events to ClickHouse",
        )

    def handle(self, *_, **options):
        """
        Creates users and triggers events for them as configured above.
        """
        start = datetime.datetime.now()
        log.info(
            f"Starting monitor for {options['backend']} with sleep of {options['sleep_time']} seconds"
        )

        monitor = Monitor(options["sleep_time"], options["backend"])
        monitor.run()

        end = datetime.datetime.now()
        log.info(f"Monitored from {start} to {end} (duration {end - start}).")
