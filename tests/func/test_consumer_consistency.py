import json
from uuid import uuid4

import psycopg
import pytest
from dramatiq import Message
from psycopg import Notify, sql

from iddqueue import PostgresBroker, generate_init_sql
from iddqueue.broker import message_lock


@pytest.fixture
def area():
    schema = "consumer_" + uuid4().hex[:10]
    with psycopg.connect("", autocommit=True) as conn:
        conn.execute(generate_init_sql(schema))
    broker = PostgresBroker(schema=schema, results=False, middleware=[])
    consumers = []
    def consumer(queue="jobs"):
        c = broker.consume(queue, prefetch=10, timeout=10)
        c.get_listen_conn()
        consumers.append(c)
        return c
    try:
        yield broker, consumer
    finally:
        for c in consumers:
            c.close()
        broker.close()
        with psycopg.connect("", autocommit=True) as conn:
            conn.execute(sql.SQL("DROP SCHEMA {} CASCADE").format(sql.Identifier(schema)))


def hint(message, full=True):
    return Notify(pid=0, channel="unused", payload=message.encode().decode() if full else
                  json.dumps({"message_id": message.message_id}))


def task(queue="jobs"):
    return Message(queue, "unused", (), {"value": "old"}, {})


def test_stale_payload(area):
    broker, consumer = area
    c = consumer()
    old = task()
    broker.enqueue(old)
    updated = old.copy(actor_name="updated", kwargs={"value": "new"}, options={"retries": 2})
    broker.enqueue(updated)
    c.notifies = [hint(old)]
    got = next(c)
    assert got.kwargs == updated.kwargs
    assert got.actor_name == "updated" and got.options["retries"] == 2


def test_moved_delay_hint(area):
    broker, consumer = area
    normal, delayed = consumer(), consumer("jobs.DQ")
    message = task()
    broker.enqueue(message)
    due = broker.enqueue(message, delay=60000)
    normal.notifies = [hint(message)]
    assert next(normal) is None
    delayed.notifies = [hint(message, full=False)]
    got = next(delayed)
    assert got.queue_name == "jobs.DQ" and got.options["eta"] == due.options["eta"]


@pytest.mark.parametrize("state", [None, "done", "rejected", "cancelled"])
def test_obsolete_hint_continues(area, state):
    broker, consumer = area
    c = consumer()
    old, valid = task().copy(kwargs={"value": "x" * 9000}), task()
    broker.enqueue(old)
    with psycopg.connect("", autocommit=True) as conn:
        table = sql.Identifier(broker.queries.schema, "queue")
        query = sql.SQL("DELETE FROM {} WHERE message_id=%s") if state is None else sql.SQL(
            "UPDATE {} SET state=%s WHERE message_id=%s")
        conn.execute(query.format(table), (old.message_id,) if state is None else (state, old.message_id))
    broker.enqueue(valid)
    c.notifies = [hint(old, full=False), hint(valid)]
    assert next(c).message_id == valid.message_id
    with psycopg.connect("", autocommit=True) as conn:
        assert conn.execute("SELECT pg_try_advisory_lock(%s)",
                            (message_lock(old, schema=broker.queries.schema),)).fetchone()[0]


@pytest.mark.parametrize("reject", [False, True])
@pytest.mark.parametrize("saturated", [False, True])
def test_completed_locks_release_with_backlog(area, reject, saturated):
    broker, consumer = area
    c = consumer()
    one, two = task(), task()
    broker.enqueue(one)
    c.notifies = [hint(one)]
    claimed = next(c)
    (c.nack if reject else c.ack)(claimed)
    broker.enqueue(two)
    c.notifies = [hint(two)]
    if saturated:
        c.prefetch = 0
    got = next(c)
    assert got is None if saturated else got.message_id == two.message_id
    assert c.unlock_q.empty()
    with psycopg.connect("", autocommit=True) as conn:
        assert conn.execute("SELECT pg_try_advisory_lock(%s)",
                            (message_lock(one, schema=broker.queries.schema),)).fetchone()[0]


@pytest.mark.parametrize("payload", ["{", "null", "[]", "1", '"hint"', "{}",
                                     '{"message_id":null}', '{"message_id":1}',
                                     '{"message_id":[]}', '{"message_id":"invalid"}',
                                     '{"scan":"true"}'])
def test_malformed_notifications_preserve_sessions_and_locks(area, payload, monkeypatch):
    broker, consumer = area
    c = consumer()
    one, two = task(), task()
    broker.enqueue(one)
    c.notifies = [hint(one)]
    assert next(c).message_id == one.message_id
    sessions = c._listen_conn, c._consume_conn
    role = "sender_" + uuid4().hex[:10]
    with psycopg.connect("", autocommit=True) as admin:
        admin.execute(sql.SQL("CREATE ROLE {} NOLOGIN").format(sql.Identifier(role)))
        try:
            with psycopg.connect("", autocommit=True) as sender:
                sender.execute(sql.SQL("SET ROLE {}").format(sql.Identifier(role)))
                assert not sender.execute("SELECT has_schema_privilege(current_user, %s, 'USAGE')",
                                          (broker.queries.schema,)).fetchone()[0]
                sender.execute("SELECT pg_notify(%s, %s)",
                               (broker.queries.channel("jobs", "enqueue"), payload))
            c.poll_for_notify()
            assert any(n.payload == payload for n in c.notifies)
            # Force legitimate control through a full hint, not periodic scanning.
            monkeypatch.setattr("iddqueue.broker.randint", lambda *args: 1)
            broker.enqueue(two)
            c.notifies.append(hint(two))
            assert next(c).message_id == two.message_id
            assert (c._listen_conn, c._consume_conn) == sessions
            assert not admin.execute("SELECT pg_try_advisory_lock(%s)",
                                    (message_lock(one, schema=broker.queries.schema),)).fetchone()[0]
        finally:
            admin.execute(sql.SQL("DROP ROLE {}").format(sql.Identifier(role)))


@pytest.mark.parametrize("alternate_durable", [False, True])
def test_scan_and_alternate_uuid_hints(area, alternate_durable):
    broker, consumer = area
    c = consumer()
    one, two = task(), task()
    if alternate_durable:
        one = one.copy(message_id=one.message_id.upper())
    broker.enqueue(one)
    c.notifies = [Notify(pid=0, channel="unused", payload=json.dumps(
        {"message_id": "{" + one.message_id.upper() + "}"}))]
    assert next(c).message_id == one.message_id
    broker.enqueue(two)
    c.notifies = [Notify(pid=0, channel="unused", payload='{"scan":true}')]
    assert next(c).message_id == two.message_id
    with psycopg.connect("", autocommit=True) as conn:
        assert not conn.execute("SELECT pg_try_advisory_lock(%s)",
                                (message_lock(one, schema=broker.queries.schema),)).fetchone()[0]

    c.notifies = [hint(one, full=False)]
    assert next(c) is None
    c.ack(one)
    c.purge_locks()
    with psycopg.connect("", autocommit=True) as conn:
        assert conn.execute("SELECT pg_try_advisory_lock(%s)",
                            (message_lock(one, schema=broker.queries.schema),)).fetchone()[0]
