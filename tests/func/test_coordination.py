import multiprocessing
import time
import uuid
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor

import dramatiq
import psycopg
import pytest
from dramatiq.rate_limits import (
    Barrier,
    BucketRateLimiter,
    ConcurrentRateLimiter,
    WindowRateLimiter,
)
from psycopg import sql

from iddqueue import (
    PostgresRateLimiterBackend,
    generate_coordination_sql,
    generate_init_sql,
)


def attempt(operation, key):
    backend = PostgresRateLimiterBackend()
    try:
        if operation == "add":
            return backend.add(key, 0, 10000)
        if operation == "incr":
            return backend.incr(key, 1, 4, 10000)
        if operation == "decr":
            return backend.decr(key, 1, 0, 10000)
        raise ValueError(operation)
    finally:
        backend.close()


def window_attempt(args):
    key, index = args
    backend = PostgresRateLimiterBackend()
    try:
        return backend.incr_and_sum(key + ("@a" if index % 2 else "@b"), lambda: [key + "@a", key + "@b"], 1, 4, 10000)
    finally:
        backend.close()


@pytest.fixture
def backend():
    backend = PostgresRateLimiterBackend()
    yield backend
    backend.close()


def test_migration_preserves_queue():
    schema = "test_" + uuid.uuid4().hex
    with psycopg.connect("", autocommit=True) as conn:
        try:
            conn.execute(generate_init_sql(schema, "p_"))
            conn.execute(sql.SQL("INSERT INTO {} (message_id) VALUES (%s)").format(sql.Identifier(schema, "p_queue")), (uuid.uuid4(),))
            conn.execute(sql.SQL("DROP TABLE {}").format(sql.Identifier(schema, "p_coordination")))
            conn.execute(generate_coordination_sql(schema, "p_"))
            conn.execute(generate_coordination_sql(schema, "p_"))
            assert conn.execute(sql.SQL("SELECT count(*) FROM {}").format(sql.Identifier(schema, "p_queue"))).fetchone()[0] == 1
            isolated = PostgresRateLimiterBackend(schema=schema, prefix="p_")
            try:
                assert isolated.add("key", 1, 1000)
            finally:
                isolated.close()
        finally:
            conn.execute(sql.SQL("DROP SCHEMA {} CASCADE").format(sql.Identifier(schema)))


def test_counters_across_processes(backend):
    key = str(uuid.uuid4())
    with ProcessPoolExecutor(4, mp_context=multiprocessing.get_context("spawn")) as executor:
        assert sum(executor.map(attempt, ["add"] * 12, [key] * 12)) == 1
        assert sum(executor.map(attempt, ["incr"] * 12, [key] * 12)) == 4
        assert sum(executor.map(attempt, ["decr"] * 12, [key] * 12)) == 4
        assert sum(executor.map(window_attempt, [(key, i) for i in range(12)])) == 4


def test_expiry_and_standard_limiters(backend, pgconn):
    key = str(uuid.uuid4())
    assert backend.add(key, 1, 10000)
    assert not backend.add(key, 2, 10000)
    with pgconn() as cursor:
        cursor.execute(sql.SQL("UPDATE {} SET expires_at = clock_timestamp() - interval '1 second' WHERE key = %s")
                       .format(backend.table), (key,))
    assert backend.add(key, 2, 1000)
    limiter = ConcurrentRateLimiter(backend, key + "mutex", limit=1)
    with limiter.acquire(raise_on_failure=False) as acquired:
        assert acquired
        with limiter.acquire(raise_on_failure=False) as nested:
            assert not nested
    with limiter.acquire() as acquired:
        assert acquired
    for cls, kwargs in [(BucketRateLimiter, {"bucket": 60000}), (WindowRateLimiter, {"window": 60})]:
        limiter = cls(backend, key + cls.__name__, limit=1, **kwargs)
        with limiter.acquire() as acquired:
            assert acquired
        with limiter.acquire(raise_on_failure=False) as acquired:
            assert not acquired


def test_durable_events(backend, pgconn):
    key = str(uuid.uuid4())
    assert not backend.wait(key, 20)
    backend.wait_notify(key, 10000)
    assert backend.wait(key, 0)
    with pgconn() as cursor:
        cursor.execute(sql.SQL("UPDATE {} SET event_expires_at = clock_timestamp() - interval '1 second' WHERE key = %s")
                       .format(backend.table), (key,))
    assert not backend.wait(key, 0)
    with ThreadPoolExecutor(2) as executor:
        waiting = executor.submit(backend.wait, key, 2000)
        time.sleep(0.05)
        backend.wait_notify(key, 1000)
        assert waiting.result(timeout=3)
    barrier = Barrier(backend, key + "barrier")
    assert barrier.create(2)
    assert not barrier.wait(block=False)
    assert barrier.wait(block=False)
    assert backend.wait(barrier.key_events, 0)


def test_group_callback(restart_worker, witness):
    from tests.func.actors import writer

    marker = str(uuid.uuid4())
    group = dramatiq.group([writer.message(part=i, marker=marker) for i in range(4)])
    group.add_completion_callback(writer.message(callback=True, marker=marker))
    group.run()
    deadline = time.monotonic() + 10
    with psycopg.connect("", autocommit=True) as conn:
        while time.monotonic() < deadline:
            rows = conn.execute("SELECT payload FROM functest.witness WHERE payload->'kwargs'->>'marker' = %s", (marker,)).fetchall()
            if any(row[0]["kwargs"].get("callback") for row in rows):
                assert len(rows) == 5
                return
            time.sleep(0.05)
    pytest.fail("Group completion callback was not executed")


def test_window_advances_while_acquiring_locks(backend):
    key = str(uuid.uuid4())
    old_key, new_key = key + "@old", key + "@new"
    assert backend.add(new_key, 1, 10000)
    windows = iter([[old_key], [new_key]])

    def current_keys():
        return next(windows, [new_key])

    assert not backend.incr_and_sum(new_key, current_keys, 1, 1, 10000)


def test_blocking_barrier_and_purge(backend):
    key = str(uuid.uuid4())
    barrier = Barrier(backend, key, ttl=10000)
    assert barrier.create(3)
    with ThreadPoolExecutor(2) as executor:
        waiters = [executor.submit(barrier.wait, timeout=2000) for _ in range(2)]
        time.sleep(0.05)
        assert barrier.wait(block=False)
        assert all(future.result(timeout=3) for future in waiters)
    expired = key + "expired"
    assert backend.add(expired, 1, 0)
    backend.wait_notify(expired, 0)
    assert backend.purge() >= 1
    assert backend.add(expired, 1, 1000)
    assert backend.wait(barrier.key_events, 0)
