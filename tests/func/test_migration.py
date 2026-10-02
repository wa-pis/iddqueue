import threading
from concurrent.futures import ThreadPoolExecutor
from uuid import uuid4

import pytest
from dramatiq import Message
from dramatiq.results import ResultMissing, ResultTimeout

from iddqueue import PostgresBackend, PostgresBroker
from iddqueue.broker import message_lock
from iddqueue.utils import getconn, make_pool, transaction


def message():
    return Message("default", "unused", (), {}, {})


@pytest.fixture
def pool():
    pool = make_pool("")
    yield pool
    pool.close()


def test_transaction_preserves_connection_and_rolls_back(pool):
    conn = getconn(pool)
    try:
        with pytest.raises(ValueError):
            with transaction(conn) as curs:
                curs.execute("CREATE TEMP TABLE rolled_back (value int)")
                raise ValueError("rollback")
        assert not conn.closed
        with transaction(conn) as curs:
            curs.execute("SELECT to_regclass('pg_temp.rolled_back')")
            assert curs.fetchone() == (None,)
    finally:
        pool.putconn(conn)


def test_result_ttl_and_timezone(pool):
    backend = PostgresBackend(pool=pool)
    task = message()
    with transaction(pool) as curs:
        curs.execute("SET TIME ZONE 'Europe/Samara'")
    backend.store_result(task, {"ok": True}, ttl=60_000)
    assert backend.get_result(task) == {"ok": True}
    backend.store_result(task, "expired", ttl=-1)
    with pytest.raises(ResultMissing):
        backend.get_result(task)


def test_large_blocking_result(pool, monkeypatch):
    import iddqueue.results as results

    backend = PostgresBackend(pool=pool)
    task = message()
    waiting = threading.Event()
    original = results.wait_for_notifies

    def wait(conn, timeout):
        waiting.set()
        return original(conn, timeout)

    monkeypatch.setattr(results, "wait_for_notifies", wait)
    payload = {"value": "ж" * 10_000}
    with ThreadPoolExecutor(max_workers=1) as executor:
        future = executor.submit(backend.get_result, task, block=True, timeout=2000)
        assert waiting.wait(1)
        backend.store_result(task, payload, ttl=60_000)
        assert future.result(timeout=3) == payload


def test_subsecond_and_zero_timeout(pool):
    import time

    backend = PostgresBackend(pool=pool)
    task = message()
    started = time.monotonic()
    with pytest.raises(ResultTimeout):
        backend.get_result(task, block=True, timeout=100)
    elapsed = time.monotonic() - started
    assert 0.08 <= elapsed < 0.8
    with pytest.raises(ResultTimeout):
        backend.get_result(task, block=True, timeout=0)


def test_requeue_and_close_release_locks(pool):
    broker = PostgresBroker(pool=pool, results=False)
    task = broker.enqueue(message().copy(queue_name=f"migration-{uuid4()}"))
    consumer = broker.consume(task.queue_name, timeout=100)
    assert consumer.consume_one(task)
    consumer.requeue([task])
    consumer.close()
    with transaction(pool) as curs:
        curs.execute("SELECT pg_try_advisory_lock(%s)", (message_lock(task),))
        assert curs.fetchone() == (True,)
        curs.execute("SELECT pg_advisory_unlock_all()")
        curs.execute(
            "SELECT state FROM dramatiq.queue WHERE message_id = %s", (task.message_id,)
        )
        assert curs.fetchone() == ("queued",)
        curs.execute(
            "DELETE FROM dramatiq.queue WHERE message_id = %s", (task.message_id,)
        )


def test_large_message_notification(pool):
    broker = PostgresBroker(pool=pool, results=False)
    queue = f"migration-{uuid4()}"
    consumer = broker.consume(queue, timeout=100)
    try:
        # Subscribe before enqueue so the message takes the NOTIFY path.
        consumer.get_listen_conn()
        payload = {"value": "ж" * 10_000}
        task = broker.enqueue(message().copy(queue_name=queue, kwargs=payload))
        received = next(consumer)
        assert received.message_id == task.message_id
        assert received.kwargs == payload
        consumer.ack(received)
        consumer.purge_locks()
    finally:
        consumer.close()


def test_external_pool_restores_autocommit_and_subscriptions():
    from psycopg_pool import ConnectionPool

    with ConnectionPool("", min_size=0, max_size=1) as pool:
        with transaction(pool, listen="migration-channel") as curs:
            assert curs.connection.autocommit
            curs.execute("SELECT 1")
        conn = getconn(pool)
        try:
            assert not conn.autocommit
            with transaction(conn) as curs:
                curs.execute("SELECT * FROM pg_listening_channels()")
                assert curs.fetchall() == []
        finally:
            pool.putconn(conn)
