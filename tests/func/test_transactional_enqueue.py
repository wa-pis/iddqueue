from uuid import uuid4

import psycopg
import pytest
from dramatiq import Message
from dramatiq.common import current_millis, dq_name
from dramatiq.middleware import Middleware
from psycopg import sql
from psycopg.pq import TransactionStatus

from iddqueue import PostgresBroker


@pytest.fixture
def broker():
    broker = PostgresBroker(results=False, middleware=[])
    yield broker
    broker.close()


def task():
    return Message(f"txn-{uuid4()}", "unused", (), {"value": "ж" * 10000}, {})


@pytest.mark.parametrize("commit", [True, False])
def test_atomic_business_data_and_notification(broker, commit):
    message = task()
    with psycopg.connect("", autocommit=True) as observer:
        observer.execute(
            "CREATE TABLE IF NOT EXISTS public.transaction_witness (id uuid PRIMARY KEY)"
        )
        observer.execute(
            sql.SQL("LISTEN {}").format(
                sql.Identifier(f"dramatiq.{message.queue_name}.enqueue")
            )
        )
        with psycopg.connect("", autocommit=True) as connection:
            with connection.transaction(force_rollback=not commit):
                connection.execute(
                    "INSERT INTO public.transaction_witness VALUES (%s)",
                    (message.message_id,),
                )
                returned = broker.enqueue_in_transaction(message, connection=connection)
                assert returned == message
                assert not connection.closed
                assert connection.info.transaction_status == TransactionStatus.INTRANS
                assert observer.execute(
                    "SELECT count(*) FROM dramatiq.queue WHERE message_id = %s",
                    (message.message_id,),
                ).fetchone() == (0,)
                assert list(observer.notifies(timeout=0)) == []
            assert not connection.closed
            assert connection.info.transaction_status == TransactionStatus.IDLE
        for table in ("dramatiq.queue", "public.transaction_witness"):
            query = sql.SQL("SELECT count(*) FROM {} WHERE {} = %s").format(
                sql.SQL(table),
                sql.Identifier("message_id" if table == "dramatiq.queue" else "id"),
            )
            assert observer.execute(query, (message.message_id,)).fetchone() == (
                int(commit),
            )
        notifications = list(observer.notifies(timeout=0.1, stop_after=1))
        assert len(notifications) == int(commit)
        observer.execute("DROP TABLE public.transaction_witness")


@pytest.mark.parametrize("autocommit", [True, False])
def test_requires_active_transaction(broker, autocommit):
    with psycopg.connect("", autocommit=autocommit) as connection:
        with pytest.raises(ValueError, match="active transaction"):
            broker.enqueue_in_transaction(task(), connection=connection)
        assert connection.info.transaction_status == TransactionStatus.IDLE


def test_delayed_enqueue_and_hooks(broker):
    events = []

    class Hooks(Middleware):
        def before_enqueue(self, broker, message, delay):
            events.append(("before", message.queue_name, delay))

        def after_enqueue(self, broker, message, delay):
            events.append(("after", message.queue_name, delay))

    broker.add_middleware(Hooks())
    message = task()
    started = current_millis()
    with psycopg.connect("", autocommit=True) as connection:
        with connection.transaction(force_rollback=True):
            delayed = broker.enqueue_in_transaction(
                message, connection=connection, delay=1000
            )
            assert delayed.queue_name == dq_name(message.queue_name)
            assert delayed.options["eta"] >= started + 1000
            stored = connection.execute(
                "SELECT message FROM dramatiq.queue WHERE message_id = %s",
                (message.message_id,),
            ).fetchone()[0]
            assert stored["queue_name"] == delayed.queue_name
            assert stored["kwargs"] == message.kwargs
            assert events == [
                ("before", message.queue_name, 1000),
                ("after", delayed.queue_name, 1000),
            ]


def test_connection_error_is_not_retried(broker, monkeypatch):
    calls = []

    def fail(curs, message):
        calls.append(message.message_id)
        raise psycopg.OperationalError("connection lost")

    monkeypatch.setattr(broker, "_write_enqueue", fail)
    with psycopg.connect("", autocommit=True) as connection:
        with connection.transaction():
            with pytest.raises(psycopg.OperationalError, match="connection lost"):
                broker.enqueue_in_transaction(task(), connection=connection)
            assert len(calls) == 1
            assert not connection.closed
