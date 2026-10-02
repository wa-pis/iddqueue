import json
import subprocess
import threading
from concurrent.futures import ThreadPoolExecutor
from uuid import uuid4

import dramatiq
import psycopg
import pytest
from dramatiq import Message
from dramatiq.middleware import Middleware, SkipMessage
from dramatiq.results import ResultMissing
from dramatiq.worker import Worker
from psycopg import sql

from iddqueue import PostgresBroker, generate_init_sql, generate_upgrade_sql
from iddqueue.control import allow_start


@pytest.fixture
def area():
    schema = 'control"' + uuid4().hex[:10]
    prefix = 'jobs"_'
    with psycopg.connect("", autocommit=True) as conn:
        conn.execute(generate_init_sql(schema, prefix))
    broker = PostgresBroker(schema=schema, prefix=prefix, queue_control=True)
    try:
        yield broker, schema, prefix
    finally:
        broker.close()
        with psycopg.connect("", autocommit=True) as conn:
            conn.execute(sql.SQL("DROP SCHEMA {} CASCADE").format(sql.Identifier(schema)))


@pytest.mark.parametrize("delay", [None, 1000])
def test_pause_resume_restart_and_cli(area, delay):
    broker, schema, prefix = area
    queue = "paused-" + uuid4().hex
    message = broker.enqueue(Message(queue, "unused", (), {}, {}), delay=delay)
    consumer = broker.consume(message.queue_name, timeout=10)
    flags = ["iddqueue", "--schemaname", schema, "--prefix", prefix]
    try:
        out = subprocess.run([*flags, "pause", queue], check=True, capture_output=True, text=True)
        assert json.loads(out.stdout)["paused"]
        assert next(consumer) is None
        replacement = PostgresBroker(schema=schema, prefix=prefix, queue_control=True)
        try:
            assert replacement.queue_is_paused(message.queue_name)
        finally:
            replacement.close()
        other = broker.consume("independent", timeout=10)
        try:
            broker.enqueue(Message("independent", "unused", (), {}, {}))
            assert next(other) is not None
        finally:
            other.close()
        subprocess.run([*flags, "resume", message.queue_name], check=True, capture_output=True)
        resumed = next(consumer)
        assert resumed.message_id == message.message_id
        assert resumed.options == message.options
        consumer.ack(resumed)
        with psycopg.connect("", autocommit=True) as conn:
            conn.execute(generate_upgrade_sql(schema, prefix))
            conn.execute(generate_upgrade_sql(schema, prefix))
        assert not broker.queue_is_paused(queue)
    finally:
        consumer.close()


def test_pause_waits_for_start_gate(area):
    broker, schema, prefix = area
    attempted = threading.Event()
    finished = threading.Event()
    with ThreadPoolExecutor(max_workers=1) as executor, psycopg.connect("", autocommit=True) as conn:
        with conn.transaction():
            assert allow_start(conn.cursor(), "jobs", schema, prefix)

            def pause():
                attempted.set()
                broker.pause_queue("jobs")
                finished.set()

            future = executor.submit(pause)
            assert attempted.wait(2)
            assert not finished.wait(0.1)
        future.result(timeout=5)
    assert broker.queue_is_paused("jobs")
    with psycopg.connect("", autocommit=True) as conn, conn.transaction():
        assert not allow_start(conn.cursor(), "jobs", schema, prefix)


def test_prefetched_pause_preserves_results_and_retries(area):
    broker, schema, prefix = area
    started = threading.Event()
    release = threading.Event()
    claimed_second = threading.Event()
    deferred = threading.Event()
    second_started = threading.Event()

    class Observe(Middleware):
        def after_ack(self, broker, message):
            if getattr(message, "_pg_paused", False):
                deferred.set()

    broker.add_middleware(Observe())

    @dramatiq.actor(broker=broker, queue_name="prefetch", store_results=True)
    def first():
        started.set()
        assert release.wait(10)
        return "first"

    @dramatiq.actor(broker=broker, queue_name="prefetch", store_results=True)
    def second():
        second_started.set()
        return "second"

    original = broker.consume

    def consume(*args, **kwargs):
        consumer = original(*args, **kwargs)
        original_claim = consumer.consume_one

        def claim(message):
            result = original_claim(message)
            if result and message.actor_name == "second":
                claimed_second.set()
            return result

        consumer.consume_one = claim
        return consumer

    broker.consume = consume
    worker = Worker(broker, worker_threads=1, worker_timeout=20)
    worker.start()
    try:
        one = first.send()
        assert started.wait(5)
        two = second.send()
        assert claimed_second.wait(5)
        broker.pause_queue("prefetch")
        release.set()
        assert deferred.wait(5)
        assert not second_started.is_set()
        assert one.get_result(backend=broker.backend, block=True, timeout=5000) == "first"
        with pytest.raises(ResultMissing):
            two.get_result(backend=broker.backend)
        with psycopg.connect("", autocommit=True) as conn:
            row = conn.execute(sql.SQL(
                "SELECT state, message FROM {} WHERE message_id = %s"
            ).format(sql.Identifier(schema, prefix + "queue")), (two.message_id,)).fetchone()
            assert row[0] == "queued"
            assert "retries" not in row[1]["options"]
        worker.stop(timeout=5000)
        worker = Worker(broker, worker_threads=1, worker_timeout=20)
        worker.start()
        assert broker.queue_is_paused("prefetch")
        assert not second_started.is_set()
        broker.resume_queue("prefetch")
        assert two.get_result(backend=broker.backend, block=True, timeout=5000) == "second"
    finally:
        release.set()
        worker.stop(timeout=5000)


def test_gate_fails_closed(area, monkeypatch):
    broker, _, _ = area
    proxy = dramatiq.broker.MessageProxy(Message("jobs", "unused", (), {}, {}))

    def unavailable(*args):
        raise psycopg.OperationalError("offline")

    monkeypatch.setattr("iddqueue.control.allow_start", unavailable)
    with pytest.raises(SkipMessage):
        broker.emit_before("process_message", proxy)
    assert proxy._pg_paused


def test_resume_before_deferred_ack_still_wakes(area):
    broker, _, _ = area
    owner = broker.consume("resume-race", timeout=10)
    observer = broker.consume("resume-race", timeout=10)
    message = broker.enqueue(Message("resume-race", "unused", (), {}, {}))
    try:
        claimed = next(owner)
        broker.pause_queue("resume-race")
        with pytest.raises(SkipMessage):
            broker.emit_before("process_message", claimed)
        broker.resume_queue("resume-race")
        assert next(observer) is None
        owner.ack(claimed)
        owner.purge_locks()
        assert next(observer).message_id == message.message_id
    finally:
        owner.close()
        observer.close()


def test_control_storage_isolation(area):
    broker, schema, prefix = area
    other = PostgresBroker(schema=schema, prefix=prefix + "other_", queue_control=True)
    try:
        with psycopg.connect("", autocommit=True) as conn:
            conn.execute(generate_init_sql(schema, prefix + "other_"))
        broker.pause_queue("jobs")
        assert not other.queue_is_paused("jobs")
        other.resume_queue("jobs")
        assert broker.queue_is_paused("jobs")
    finally:
        other.close()
