import threading
from concurrent.futures import ThreadPoolExecutor
from uuid import uuid4

import psycopg
import pytest
from dramatiq import Message
from dramatiq.middleware import SkipMessage
from psycopg import sql

from iddqueue import (
    PostgresBroker,
    ResultCancelled,
    generate_init_sql,
    generate_upgrade_sql,
)
from iddqueue.metrics import queue_statistics


@pytest.fixture
def area():
    schema = 'cancel"' + uuid4().hex[:10]
    prefix = 'tasks"_'
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
def test_cancel_queued_and_delayed(area, delay):
    broker, _, _ = area
    message = broker.enqueue(Message("jobs", "unused", (), {}, {}), delay=delay)
    assert broker.cancel(message.message_id)["status"] == "cancelled"
    assert broker.cancel(message.message_id)["status"] == "cancelled"
    with pytest.raises(ResultCancelled):
        broker.backend.get_result(message, block=True, timeout=100)
    consumer = broker.consume(message.queue_name, timeout=10)
    try:
        assert next(consumer) is None
        broker.enqueue(message)
        consumer.requeue([message])
        assert next(consumer) is None
        assert broker.cancellation_status(message.message_id)["state"] == "cancelled"
        snapshot = queue_statistics(broker.pool, schema=broker.queries.schema,
                                    prefix=broker.queries.prefix, queue=message.queue_name)[0]
        assert snapshot["counts"]["cancelled"] == 1
        assert snapshot["ready"] == snapshot["scheduled"] == 0
    finally:
        consumer.close()


def test_cancel_prefetched_and_stale_ack_nack(area):
    broker, _, _ = area
    message = broker.enqueue(Message("jobs", "unused", (), {}, {}))
    consumer = broker.consume("jobs", timeout=10)
    try:
        claimed = next(consumer)
        assert broker.cancel(message.message_id)["status"] == "cancelled"
        with pytest.raises(SkipMessage):
            broker.emit_before("process_message", claimed)
        broker.emit_after("skip_message", claimed)
        consumer.ack(claimed)
        # Stale terminal operations cannot overwrite the cancellation tombstone.
        consumer.in_processing.add(message.message_id)
        consumer.nack(claimed)
        assert broker.cancellation_status(message.message_id)["state"] == "cancelled"
        with pytest.raises(ResultCancelled):
            broker.backend.get_result(message)
    finally:
        consumer.close()


def test_running_request_then_retry_cancels(area):
    broker, _, _ = area
    message = broker.enqueue(Message("jobs", "unused", (), {}, {}))
    consumer = broker.consume("jobs", timeout=10)
    try:
        claimed = next(consumer)
        broker.emit_before("process_message", claimed)
        assert broker.cancel(message.message_id)["status"] == "requested"
        assert broker.cancellation_requested(message.message_id)
        # Actor sees cooperative flag; failure/retry must not start another attempt.
        broker.enqueue(message)
        consumer.ack(claimed)
        consumer.purge_locks()
        retried = next(consumer)
        with pytest.raises(SkipMessage):
            broker.emit_before("process_message", retried)
        consumer.ack(retried)
        assert broker.cancellation_status(message.message_id)["state"] == "cancelled"
    finally:
        consumer.close()


def test_missing_completed_and_isolation(area):
    broker, schema, prefix = area
    assert broker.cancel(str(uuid4()))["status"] == "missing"
    message = broker.enqueue(Message("jobs", "unused", (), {}, {}))
    consumer = broker.consume("jobs", timeout=10)
    try:
        claimed = next(consumer)
        broker.emit_before("process_message", claimed)
        broker.backend.store_result(message, "ok", 60000)
        consumer.ack(claimed)
        assert broker.cancel(message.message_id)["status"] == "terminal"
        assert broker.backend.get_result(message) == "ok"
        other = PostgresBroker(schema=schema, prefix=prefix + "other_", queue_control=True)
        try:
            with psycopg.connect("", autocommit=True) as conn:
                conn.execute(generate_init_sql(schema, prefix + "other_"))
            other.enqueue(message)
            other.cancel(message.message_id)
            assert broker.backend.get_result(message) == "ok"
        finally:
            other.close()
    finally:
        consumer.close()


def test_cancel_waits_for_start_transaction(area):
    broker, schema, prefix = area
    message = broker.enqueue(Message("jobs", "unused", (), {}, {}))
    attempting = threading.Event()
    completed = threading.Event()
    with ThreadPoolExecutor(max_workers=1) as executor, psycopg.connect("", autocommit=True) as conn:
        with conn.transaction():
            conn.execute(sql.SQL(
                "UPDATE {} SET started = TRUE, state = 'consumed' WHERE message_id = %s"
            ).format(sql.Identifier(schema, prefix + "queue")), (message.message_id,))

            def cancel():
                attempting.set()
                result = broker.cancel(message.message_id)
                completed.set()
                return result

            future = executor.submit(cancel)
            assert attempting.wait(2)
            assert not completed.wait(0.1)
        assert future.result(timeout=5)["status"] == "requested"


def test_upgrade_is_idempotent(area):
    broker, schema, prefix = area
    message = broker.enqueue(Message("jobs", "unused", (), {}, {}))
    with psycopg.connect("", autocommit=True) as conn:
        conn.execute(generate_upgrade_sql(schema, prefix))
        conn.execute(generate_upgrade_sql(schema, prefix))
    assert broker.cancel(message.message_id)["status"] == "cancelled"


def test_real_worker_prefetched_cancel_and_cooperative_request(area):
    import dramatiq
    from dramatiq.middleware import CurrentMessage
    from dramatiq.worker import Worker

    broker, _, _ = area
    broker.add_middleware(CurrentMessage())
    started = threading.Event()
    release = threading.Event()
    prefetched = threading.Event()
    second_started = threading.Event()

    @dramatiq.actor(broker=broker, queue_name="cancel-worker", store_results=True)
    def first():
        started.set()
        assert release.wait(10)
        current = CurrentMessage.get_current_message()
        return "stopped" if broker.cancellation_requested(current.message_id) else "finished"

    @dramatiq.actor(broker=broker, queue_name="cancel-worker", store_results=True)
    def second():
        second_started.set()
        return "unexpected"

    original = broker.consume

    def consume(*args, **kwargs):
        consumer = original(*args, **kwargs)
        claim = consumer.consume_one

        def observe(message):
            result = claim(message)
            if result and message.actor_name == "second":
                prefetched.set()
            return result

        consumer.consume_one = observe
        return consumer

    broker.consume = consume
    worker = Worker(broker, worker_threads=1, worker_timeout=20)
    worker.start()
    try:
        one = first.send()
        assert started.wait(5)
        two = second.send()
        assert prefetched.wait(5)
        assert broker.cancel(one.message_id)["status"] == "requested"
        assert broker.cancel(two.message_id)["status"] == "cancelled"
        release.set()
        assert one.get_result(backend=broker.backend, block=True, timeout=5000) == "stopped"
        with pytest.raises(ResultCancelled):
            two.get_result(backend=broker.backend, block=True, timeout=100)
    finally:
        release.set()
        worker.stop(timeout=5000)
    assert not second_started.is_set()


def test_cancellation_wakes_result_waiter(area):
    broker, _, _ = area
    message = broker.enqueue(Message("waiting", "unused", (), {}, {}))
    waiting = threading.Event()

    def result():
        waiting.set()
        with pytest.raises(ResultCancelled):
            broker.backend.get_result(message, block=True, timeout=5000)

    with ThreadPoolExecutor(max_workers=1) as executor:
        future = executor.submit(result)
        assert waiting.wait(2)
        broker.cancel(message.message_id)
        future.result(timeout=2)


def test_cli_cancel_and_status(area):
    import json
    import subprocess

    broker, schema, prefix = area
    message = broker.enqueue(Message("cli-cancel", "unused", (), {}, {}))
    flags = ["iddqueue", "--schemaname", schema, "--prefix", prefix]
    result = subprocess.run([*flags, "cancel", message.message_id], check=True,
                            text=True, capture_output=True)
    assert json.loads(result.stdout)["status"] == "cancelled"
    status = subprocess.run([*flags, "cancel-status", message.message_id], check=True,
                            text=True, capture_output=True)
    assert json.loads(status.stdout) == {"state": "cancelled", "requested": True}
    missing = subprocess.run([*flags, "cancel", str(uuid4())], text=True, capture_output=True)
    assert missing.returncode == 1
    assert json.loads(missing.stdout)["status"] == "missing"
