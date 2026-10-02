import json
import os
import socket
import subprocess
import time
from urllib.request import urlopen
from uuid import uuid4

import psycopg
import pytest
from dramatiq import Message, get_broker
from dramatiq.results import ResultFailure
from prometheus_client import CollectorRegistry, generate_latest
from prometheus_client.parser import text_string_to_metric_families
from psycopg.types.json import Jsonb

from example import failing, saver
from iddqueue import PostgresBroker
from iddqueue.metrics import PostgresQueueCollector, queue_statistics
from iddqueue.utils import make_pool

from .conftest import WorkerManager


def test_snapshot_delays_and_retry():
    queue = "metric-" + uuid4().hex
    pool = make_pool("")
    broker = PostgresBroker(pool=pool, results=False)
    ids = []
    try:
        assert queue_statistics(pool, queue=queue)[0]["ready"] == 0
        with psycopg.connect("", autocommit=True) as conn:
            for state, delayed in [("queued", False), ("queued", True), ("consumed", True), ("done", False), ("rejected", False)]:
                message = Message(queue_name=queue, actor_name="test", args=(), kwargs={}, options={})
                ids.append(message.message_id)
                if delayed:
                    message.options["eta"] = int((time.time() + 60) * 1000)
                conn.execute("INSERT INTO dramatiq.queue (message_id, queue_name, state, message, mtime) VALUES (%s, %s, %s, %s, now()-interval '1 hour')", (message.message_id, queue, state, Jsonb(message.asdict())))
            stats = queue_statistics(pool, queue=queue)[0]
            assert stats["counts"] == {"queued": 2, "consumed": 1, "done": 1, "rejected": 1}
            assert stats["ready"] == 1 and stats["scheduled"] == 2
            assert stats["oldest_ready_seconds"] >= 3600
            retry = Message(message_id=ids[0], queue_name=queue, actor_name="test", args=(), kwargs={}, options={"retries": 1})
            broker.enqueue(retry)
            assert 0 <= queue_statistics(pool, queue=queue)[0]["oldest_ready_seconds"] < 2
            registry = CollectorRegistry()
            registry.register(PostgresQueueCollector(pool, queue=queue))
            text = generate_latest(registry).decode()
            assert 'state="rejected"' in text
            assert 'iddqueue_queue_ready{queue="' + queue + '"} 1.0' in text
            assert "actor" not in text and "message_id" not in text
            result = subprocess.run(["iddqueue", "stats", "--queue", queue], capture_output=True, text=True, check=True)
            assert json.loads(result.stdout)[0]["scheduled"] == 2
    finally:
        with psycopg.connect("", autocommit=True) as conn:
            conn.execute("DELETE FROM dramatiq.queue WHERE message_id = ANY(%s::uuid[])", (ids,))
        pool.close()


@pytest.mark.timeout(35)
def test_standard_prometheus_processing_and_retry(tmp_path):
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        port = sock.getsockname()[1]
    queue = "prom-" + uuid4().hex[:12]
    env = dict(os.environ, EXAMPLE_QUEUE=queue, EXAMPLE_PROMETHEUS="1", dramatiq_prom_host="127.0.0.1",
               dramatiq_prom_port=str(port), dramatiq_prom_db=str(tmp_path / "prom"))
    worker = WorkerManager(name="metrics", env=env)
    try:
        worker.start()
        message = get_broker().enqueue(saver.message(metric=True).copy(queue_name=queue))
        assert message.get_result(block=True, timeout=8000) == {"metric": True}
        message = get_broker().enqueue(failing.message_with_options(max_retries=1, min_backoff=1, max_backoff=1, store_results=True).copy(queue_name=queue))
        with pytest.raises(ResultFailure):
            message.get_result(block=True, timeout=8000)
        deadline = time.monotonic() + 8
        while time.monotonic() < deadline:
            try:
                with urlopen(f"http://127.0.0.1:{port}/metrics", timeout=2) as response:
                    text = response.read().decode()
                samples = [sample for family in text_string_to_metric_families(text) for sample in family.samples]
                def value(name, actor):
                    return sum(sample.value for sample in samples if sample.name == name and sample.labels.get("actor_name") == actor)
                if value("dramatiq_message_retries_total", "failing") >= 1:
                    assert value("dramatiq_messages_total", "saver") >= 1
                    assert value("dramatiq_message_errors_total", "failing") >= 2
                    assert value("dramatiq_message_duration_milliseconds_count", "saver") >= 1
                    return
            except OSError:
                pass
            time.sleep(0.05)
        pytest.fail("Standard Prometheus processing/retry metrics missing")
    finally:
        worker.stop()
