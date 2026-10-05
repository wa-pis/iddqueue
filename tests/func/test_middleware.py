import os
import threading
import time
from queue import Queue
from uuid import uuid4

import dramatiq
import psycopg
import pytest
from dramatiq.middleware import (
    CurrentMessage,
    Middleware,
    TimeLimit,
    default_middleware,
)
from dramatiq.results import ResultFailure
from dramatiq.worker import Worker
from psycopg import sql

from iddqueue import PostgresBroker, generate_init_sql
from iddqueue.broker import message_lock
from tests.func.actors import shutdown_probe

from .conftest import WorkerManager


@pytest.fixture
def area():
    schema = 'middleware"' + uuid4().hex[:10]
    prefix = 'jobs"_'
    with psycopg.connect("", autocommit=True) as conn:
        conn.execute(generate_init_sql(schema, prefix))
    middleware = [TimeLimit(interval=20) if cls is TimeLimit else cls()
                  for cls in default_middleware]
    broker = PostgresBroker(schema=schema, prefix=prefix, middleware=middleware, queue_control=True)
    # Worker is embedded here: reproduce CLI's process boot for the real timer.
    broker.emit_after("process_boot")
    try:
        yield broker, schema, prefix
    finally:
        broker.close()
        with psycopg.connect("", autocommit=True) as conn:
            conn.execute(sql.SQL("DROP SCHEMA {} CASCADE").format(sql.Identifier(schema)))


def assert_terminal_unlocked(area, message, state):
    broker, schema, prefix = area
    deadline = time.monotonic() + 5
    lock = message_lock(message, schema=schema, prefix=prefix)
    with psycopg.connect("", autocommit=True) as conn:
        while time.monotonic() < deadline:
            row = conn.execute(sql.SQL("SELECT state::text FROM {} WHERE message_id = %s")
                               .format(sql.Identifier(schema, prefix + "queue")),
                               (message.message_id,)).fetchone()
            acquired = conn.execute("SELECT pg_try_advisory_lock(%s)", (lock,)).fetchone()[0]
            if acquired:
                conn.execute("SELECT pg_advisory_unlock(%s)", (lock,))
                if row == (state,):
                    return
            time.sleep(0.02)
    pytest.fail(f"Expected {state} with released session lock")


def test_age_limit(area):
    broker, _, _ = area
    invoked = threading.Event()

    @dramatiq.actor(broker=broker, queue_name="age", store_results=True, max_age=1000)
    def expired():
        invoked.set()
        return "unexpected"

    message = broker.enqueue(expired.message().copy(message_timestamp=0))
    worker = Worker(broker, worker_threads=1, worker_timeout=20)
    worker.start()
    try:
        with pytest.raises(ResultFailure, match="age limit"):
            message.get_result(backend=broker.backend, block=True, timeout=5000)
        assert not invoked.is_set()
        assert_terminal_unlocked(area, message, "rejected")
    finally:
        worker.stop(timeout=5000)


def test_time_limit_and_retry(area):
    broker, _, _ = area
    attempts = []

    @dramatiq.actor(broker=broker, queue_name="time-limit", store_results=True,
                    time_limit=60, max_retries=1, min_backoff=20, max_backoff=20)
    def busy():
        attempts.append(1)
        deadline = time.monotonic() + 3
        while time.monotonic() < deadline:
            pass
        return "not interrupted"

    worker = Worker(broker, worker_threads=1, worker_timeout=20)
    worker.start()
    try:
        message = busy.send()
        with pytest.raises(ResultFailure) as error:
            message.get_result(backend=broker.backend, block=True, timeout=5000)
        assert error.value.orig_exc_type == "TimeLimitExceeded"
        assert len(attempts) == 2
        assert_terminal_unlocked(area, message, "rejected")
    finally:
        worker.stop(timeout=5000)


def test_callbacks_include_retry_failures(area):
    broker, _, _ = area
    received = Queue()

    @dramatiq.actor(broker=broker, queue_name="callbacks")
    def callback(original, value):
        received.put((original, value))

    @dramatiq.actor(broker=broker, queue_name="callbacks", store_results=True,
                    max_retries=1, min_backoff=20, max_backoff=20,
                    on_success="callback", on_failure="callback")
    def operation(fail):
        if fail:
            raise ValueError("middleware failure")
        return {"ok": True}

    worker = Worker(broker, worker_threads=1, worker_timeout=20)
    worker.start()
    try:
        successful = operation.send(False)
        assert successful.get_result(backend=broker.backend, block=True, timeout=5000) == {"ok": True}
        original, value = received.get(timeout=5)
        assert original["message_id"] == successful.message_id
        assert value == {"ok": True}
        failing = operation.send(True)
        with pytest.raises(ResultFailure):
            failing.get_result(backend=broker.backend, block=True, timeout=5000)
        for _ in range(2):
            original, value = received.get(timeout=5)
            assert original["message_id"] == failing.message_id
            assert value == {"type": "ValueError", "message": "middleware failure"}
        assert_terminal_unlocked(area, failing, "rejected")
    finally:
        worker.stop(timeout=5000)


def test_current_message_context_cleanup(area):
    broker, _, _ = area
    outside = []

    class Observe(Middleware):
        def before_process_message(self, broker, message):
            outside.append(CurrentMessage.get_current_message())

        def after_process_message(self, broker, message, **kwargs):
            outside.append(CurrentMessage.get_current_message())

    broker.add_middleware(Observe())
    broker.add_middleware(CurrentMessage())

    @dramatiq.actor(broker=broker, queue_name="current", store_results=True, max_retries=0)
    def inspect(fail=False):
        current = CurrentMessage.get_current_message()
        if fail:
            raise ValueError("context failure")
        return {"id": current.message_id, "marker": current.options["marker"]}

    worker = Worker(broker, worker_threads=1, worker_timeout=20)
    worker.start()
    try:
        failing = inspect.send(True)
        with pytest.raises(ResultFailure):
            failing.get_result(backend=broker.backend, block=True, timeout=5000)
        for marker in ["first", "second"]:
            message = inspect.send_with_options(marker=marker)
            assert message.get_result(backend=broker.backend, block=True, timeout=5000) == {
                "id": message.message_id, "marker": marker}
        assert outside and all(value is None for value in outside)
        assert CurrentMessage.get_current_message() is None
    finally:
        worker.stop(timeout=5000)


@pytest.mark.timeout(35)
def test_shutdown_notification_real_process():
    marker = uuid4().hex
    queue = "shutdown-" + marker[:12]
    worker = WorkerManager(name="middleware-shutdown", env=dict(
        os.environ, EXAMPLE_QUEUE=queue, EXAMPLE_QUEUE_CONTROL="1"))
    broker = dramatiq.get_broker()
    worker.start()
    try:
        message = broker.enqueue(shutdown_probe.message(marker).copy(queue_name=queue))
        deadline = time.monotonic() + 8
        with psycopg.connect("", autocommit=True) as conn:
            while time.monotonic() < deadline:
                if conn.execute("SELECT 1 FROM functest.witness WHERE payload->>'shutdown_started' = %s",
                                (marker,)).fetchone():
                    break
                time.sleep(0.02)
            else:
                pytest.fail("Shutdown actor never started")
        worker.stop()
        assert message.get_result(block=True, timeout=5000) == "shutdown"
        with psycopg.connect("", autocommit=True) as conn:
            assert conn.execute(
                "SELECT 1 FROM functest.witness WHERE payload->>'shutdown_cleanup' = %s",
                (marker,)).fetchone()
            assert conn.execute("SELECT state::text FROM dramatiq.queue WHERE message_id = %s",
                                (message.message_id,)).fetchone() == ("done",)
            lock = message_lock(message)
            assert conn.execute("SELECT pg_try_advisory_lock(%s)", (lock,)).fetchone()[0]
            conn.execute("SELECT pg_advisory_unlock(%s)", (lock,))
    finally:
        if worker.proc.poll() is None:
            worker.stop()
