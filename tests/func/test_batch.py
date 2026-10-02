from uuid import uuid4

import psycopg
import pytest
from dramatiq import Message
from dramatiq.common import current_millis
from dramatiq.middleware import Middleware
from psycopg import sql
from psycopg.pq import TransactionStatus

from iddqueue import PostgresBroker, generate_init_sql


@pytest.fixture
def area():
    schema = 'batch"' + uuid4().hex[:10]
    prefix = 'jobs"_'
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


def count(conn, area, name):
    return conn.execute(sql.SQL("SELECT count(*) FROM {}")
                        .format(sql.Identifier(area[1], area[2] + name))).fetchone()[0]


@pytest.mark.parametrize("commit", [True, False])
def test_external_commit_delay_notifications(area, commit):
    broker, _, _ = area
    messages = [task("first"), task("second"), task("first")]
    options = [{}, {"delay": 1000}, {}]
    events = []

    class Hooks(Middleware):
        def before_enqueue(self, broker, message, delay):
            events.append(("before", message.message_id, delay))

        def after_enqueue(self, broker, message, delay):
            events.append(("after", message.message_id, delay))

    broker.add_middleware(Hooks())
    started = current_millis()
    with psycopg.connect("", autocommit=True) as observer, psycopg.connect("", autocommit=True) as conn:
        for queue in ["first", "second.DQ"]:
            observer.execute(sql.SQL("LISTEN {}").format(sql.Identifier(broker.queries.channel(queue, "enqueue"))))
        with conn.transaction(force_rollback=not commit):
            returned = broker.enqueue_many_in_transaction(messages, connection=conn, options=options)
            assert [m.message_id for m in returned] == [m.message_id for m in messages]
            assert returned[1].queue_name == "second.DQ"
            assert returned[1].options["eta"] >= started + 1000
            assert count(conn, area, "queue") == 3
            assert count(observer, area, "queue") == 0
            assert list(observer.notifies(timeout=0)) == []
            assert conn.info.transaction_status == TransactionStatus.INTRANS
        assert count(observer, area, "queue") == 3 * commit
        notices = list(observer.notifies(timeout=0.1))
        assert len(notices) == 3 * commit
        assert not conn.closed
        assert conn.info.transaction_status == TransactionStatus.IDLE
    assert events == [("before", m.message_id, o.get("delay")) for m, o in zip(messages, options)] + [
        ("after", m.message_id, o.get("delay")) for m, o in zip(messages, options)]


@pytest.mark.parametrize("external", [True, False])
@pytest.mark.parametrize("dedup", [True, False])
def test_batch_error_rolls_back_all(area, external, dedup):
    broker, _, _ = area
    messages = [task(), task(), task()]
    options = None
    if dedup:
        options = [{"deduplication_key": str(i), "deduplication_ttl": 60000} for i in range(3)]
        options[2]["deduplication_ttl"] = -1
        expected = ValueError
    else:
        messages[2] = messages[2].copy(message_id="invalid-uuid")
        expected = psycopg.errors.InvalidTextRepresentation
    with psycopg.connect("", autocommit=True) as conn:
        if external:
            with conn.transaction():
                broker.enqueue_in_transaction(task("caller"), connection=conn)
                with pytest.raises(expected):
                    broker.enqueue_many_in_transaction(messages, connection=conn, options=options)
                assert conn.info.transaction_status == TransactionStatus.INTRANS
                assert conn.execute("SELECT 42").fetchone() == (42,)
                # Savepoint failure does not discard an earlier caller write.
                assert count(conn, area, "queue") == 1
        else:
            with pytest.raises(expected):
                broker.enqueue_many(messages, options=options)
        assert count(conn, area, "queue") == int(external)
        assert count(conn, area, "deduplication") == 0


def test_dedup_duplicates_and_mixed_batch(area):
    broker, _, _ = area
    events = []

    class Hooks(Middleware):
        def before_enqueue(self, broker, message, delay):
            events.append(("before", message.message_id))

        def after_enqueue(self, broker, message, delay):
            events.append(("after", message.message_id))

    broker.add_middleware(Hooks())
    messages = [task(value=i) for i in range(3)]
    key = {"deduplication_key": "same", "deduplication_ttl": 60000, "delay": 1000}
    returned = broker.enqueue_many(messages, options=[key, key, {}])
    assert returned[0] == returned[1]
    assert returned[0].message_id == messages[0].message_id
    assert returned[0].kwargs == {"value": 0}
    assert returned[2] == messages[2]
    assert events == [("before", messages[0].message_id), ("before", messages[2].message_id),
                      ("after", messages[0].message_id), ("after", messages[2].message_id)]
    assert broker.enqueue_many([task()], options=[key])[0] == returned[0]
    with psycopg.connect("", autocommit=True) as conn:
        assert count(conn, area, "queue") == 2
        assert count(conn, area, "deduplication") == 1


def test_empty_validation_and_no_database_access(area, monkeypatch):
    broker, _, _ = area
    monkeypatch.setattr(broker.pool, "getconn", lambda: pytest.fail("unexpected database access"))
    assert broker.enqueue_many(iter([])) == []
    with pytest.raises(ValueError, match="1000"):
        broker.enqueue_many(task() for _ in range(1001))
    with pytest.raises(ValueError, match="match"):
        broker.enqueue_many([task()], options=[])
    with pytest.raises(ValueError, match="invalid"):
        broker.enqueue_many([task()], options=[{"unknown": True}])
    with psycopg.connect("", autocommit=True) as conn:
        with pytest.raises(ValueError, match="active transaction"):
            broker.enqueue_many_in_transaction([], connection=conn)
        with conn.transaction():
            assert broker.enqueue_many_in_transaction([], connection=conn) == []
            assert conn.info.transaction_status == TransactionStatus.INTRANS
