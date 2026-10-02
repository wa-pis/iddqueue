from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
from uuid import UUID, uuid4

import psycopg
import pytest
from dramatiq import Message
from dramatiq.middleware import Middleware
from psycopg import sql

from iddqueue import PostgresBroker, generate_init_sql, generate_upgrade_sql


@pytest.fixture(params=["", 'jobs"_'])
def area(request):
    schema = 'dedup"' + uuid4().hex[:10]
    prefix = request.param
    with psycopg.connect("", autocommit=True) as conn:
        conn.execute(generate_init_sql(schema, prefix))
    broker = PostgresBroker(schema=schema, prefix=prefix, results=False, middleware=[])
    try:
        yield broker, schema, prefix
    finally:
        broker.close()
        with psycopg.connect("", autocommit=True) as conn:
            conn.execute(sql.SQL("DROP SCHEMA {} CASCADE").format(sql.Identifier(schema)))


def task(queue="jobs", value=1):
    return Message(queue, "unused", (), {"value": value}, {})


def publish(broker, message, **kwargs):
    return broker.enqueue(message, deduplication_key="key", deduplication_ttl=60000, **kwargs)


def test_concurrent_producers_and_hooks(area):
    broker, schema, prefix = area
    barrier = Barrier(2)
    events = []

    class Hooks(Middleware):
        def before_enqueue(self, broker, message, delay):
            events.append("before")

        def after_enqueue(self, broker, message, delay):
            events.append("after")

    broker.add_middleware(Hooks())

    def send(value):
        barrier.wait(timeout=5)
        return publish(broker, task(value=value), delay=1000)

    with ThreadPoolExecutor(max_workers=2) as executor:
        results = list(executor.map(send, [1, 2]))
    assert results[0] == results[1]
    assert results[0].queue_name == "jobs.DQ"
    assert events == ["before", "after"]
    with psycopg.connect("", autocommit=True) as conn:
        table = sql.Identifier(schema, prefix + "queue")
        assert conn.execute(sql.SQL("SELECT count(*) FROM {}").format(table)).fetchone() == (1,)
        stored = conn.execute(sql.SQL("SELECT message FROM {}").format(table)).fetchone()[0]
        assert stored["kwargs"] == results[0].kwargs
        assert stored["options"]["eta"] == results[0].options["eta"]
        # Purging the task does not release its unexpired deduplication key.
        conn.execute(sql.SQL("DELETE FROM {}").format(table))
    assert publish(broker, task(value=99)) == results[0]


def test_expiry_queue_and_storage_isolation(area):
    broker, schema, prefix = area
    first = publish(broker, task())
    assert publish(broker, task("other")).message_id != first.message_id
    other = PostgresBroker(schema=schema, prefix=prefix + "other_", results=False)
    with psycopg.connect("", autocommit=True) as conn:
        conn.execute(generate_init_sql(schema, prefix + "other_"))
        table = sql.Identifier(schema, prefix + "deduplication")
        conn.execute(sql.SQL("UPDATE {} SET expires_at = '-infinity'").format(table))
    try:
        assert publish(other, task()).message_id != first.message_id
        assert publish(broker, task()).message_id != first.message_id
    finally:
        other.close()


def test_rollback_and_savepoint(area, monkeypatch):
    broker, schema, prefix = area
    message = task()
    with psycopg.connect("", autocommit=True) as conn:
        with conn.transaction(force_rollback=True):
            broker.enqueue_in_transaction(message, connection=conn,
                deduplication_key="key", deduplication_ttl=60000)
        table = sql.Identifier(schema, prefix + "deduplication")
        assert conn.execute(sql.SQL("SELECT count(*) FROM {}").format(table)).fetchone() == (0,)
        original = broker._write_enqueue

        def fail(cursor, message):
            original(cursor, message)
            raise RuntimeError("after write")

        with conn.transaction():
            with monkeypatch.context() as patch:
                patch.setattr(broker, "_write_enqueue", fail)
                with pytest.raises(RuntimeError, match="after write"):
                    broker.enqueue_in_transaction(message, connection=conn,
                        deduplication_key="key", deduplication_ttl=60000)
            assert conn.execute(sql.SQL("SELECT count(*) FROM {}").format(table)).fetchone() == (0,)
            queued = sql.Identifier(schema, prefix + "queue")
            assert conn.execute(sql.SQL("SELECT count(*) FROM {}").format(queued)).fetchone() == (0,)
            returned = broker.enqueue_in_transaction(message, connection=conn,
                deduplication_key="key", deduplication_ttl=60000)
        assert publish(broker, task()) == returned


def test_idempotent_upgrade_preserves_queue(area):
    broker, schema, prefix = area
    message = broker.enqueue(task())
    with psycopg.connect("", autocommit=True) as conn:
        conn.execute(sql.SQL("DROP TABLE {}").format(sql.Identifier(schema, prefix + "deduplication")))
        conn.execute(generate_upgrade_sql(schema, prefix))
        conn.execute(generate_upgrade_sql(schema, prefix))
        assert conn.execute(sql.SQL("SELECT message_id FROM {}").format(
            sql.Identifier(schema, prefix + "queue"))).fetchone() == (UUID(message.message_id),)


@pytest.mark.parametrize("key,ttl", [("", 1), (None, 1), ("key", None), ("key", 0), ("key", True)])
def test_invalid_deduplication_input(key, ttl):
    broker = PostgresBroker(results=False)
    try:
        # Validate before any write; no DB setup necessary.
        with pytest.raises(ValueError):
            broker._enqueue_deduplicated(None, task(), None, key, ttl)
    finally:
        broker.close()


def test_notification_waits_for_outer_commit(area):
    broker, schema, prefix = area
    message = task()
    channel = broker.queries.channel(message.queue_name, "enqueue")
    with psycopg.connect("", autocommit=True) as listener, psycopg.connect("", autocommit=True) as conn:
        listener.execute(sql.SQL("LISTEN {}").format(sql.Identifier(channel)))
        with conn.transaction():
            result = broker.enqueue_in_transaction(message, connection=conn,
                deduplication_key="key", deduplication_ttl=60000)
            assert list(listener.notifies(timeout=0)) == []
        assert len(list(listener.notifies(timeout=0.1, stop_after=1))) == 1
        assert publish(broker, task(value=99)) == result
        assert list(listener.notifies(timeout=0.05)) == []
