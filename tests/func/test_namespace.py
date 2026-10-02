import multiprocessing
from uuid import uuid4

import psycopg
import pytest
from dramatiq import Message
from psycopg import sql

from dramatiq_pg import PostgresBroker, PostgresRateLimiterBackend, generate_init_sql
from dramatiq_pg.metrics import queue_statistics
from dramatiq_pg.utils import notification_channel


def consume_namespace(schema, prefix, output, release):
    broker = PostgresBroker(schema=schema, prefix=prefix)
    consumer = broker.consume("same", timeout=1000)
    fetched = []
    original = consumer.fetch_by_id
    def fetch(message_id):
        fetched.append(message_id)
        return original(message_id)
    consumer.fetch_by_id = fetch
    try:
        consumer.get_listen_conn()
        output.put(("listening", (schema, prefix)))
        message = next(consumer)
        if message is None:
            raise AssertionError("No isolated notification received")
        broker.backend.store_result(message, message.kwargs["value"], ttl=10000)
        result = broker.backend.get_result(message, block=True, timeout=2000)
        output.put(("claimed", (schema, prefix), result, len(fetched)))
        assert release.wait(10)
        consumer.ack(message)
    finally:
        consumer.close()
        broker.close()


@pytest.mark.parametrize("separate_schema", [False, True])
def test_two_processes_same_uuid_large_payload(separate_schema):
    schema = 'isolation"' + uuid4().hex[:10]
    prefixes = ['a"_', 'b"_']
    namespaces = [(schema, prefix) for prefix in prefixes]
    if separate_schema:
        namespaces = [(schema + suffix, prefixes[0]) for suffix in ("a", "b")]
    brokers = []
    processes = []
    context = multiprocessing.get_context("spawn")
    output = context.Queue()
    release = context.Event()
    with psycopg.connect("", autocommit=True) as conn:
        try:
            for area, prefix in namespaces:
                conn.execute(generate_init_sql(area, prefix))
                brokers.append(PostgresBroker(schema=area, prefix=prefix))
            for area, prefix in namespaces:
                process = context.Process(target=consume_namespace, args=(area, prefix, output, release))
                process.start()
                processes.append(process)
            assert {output.get(timeout=10) for _ in prefixes} == {("listening", namespace) for namespace in namespaces}
            message_id = str(uuid4())
            values = ["a" * 12000, "b" * 12000]
            for broker, value in zip(brokers, values):
                broker.enqueue(Message(queue_name="same", actor_name="actor", message_id=message_id,
                                       args=(), kwargs={"value": value}, options={}))
            results = [output.get(timeout=10) for _ in prefixes]
            assert {row[1] for row in results} == set(namespaces)
            for status, namespace, value, fetched in results:
                assert status == "claimed"
                assert value == values[namespaces.index(namespace)]
                assert fetched == 1
            # Both consumers hold the same UUID concurrently, in distinct namespaces.
            release.set()
            for process in processes:
                process.join(10)
                assert process.exitcode == 0
            for broker, (area, prefix), value in zip(brokers, namespaces, values):
                message = Message(queue_name="same", actor_name="actor", message_id=message_id, args=(), kwargs={}, options={})
                assert broker.backend.get_result(message) == value
                assert queue_statistics(broker.pool, schema=area, prefix=prefix, queue="same")[0]["counts"]["done"] == 1
            limits = [PostgresRateLimiterBackend(pool=broker.pool, schema=area, prefix=prefix) for broker, (area, prefix) in zip(brokers, namespaces)]
            assert all(backend.add("same", 1, 10000) for backend in limits)
            limits[0].wait_notify("event", 10000)
            assert limits[0].wait("event", 0)
            assert not limits[1].wait("event", 0)
        finally:
            release.set()
            for process in processes:
                process.join(3)
                if process.is_alive():
                    process.terminate()
                    process.join(3)
            for broker in brokers:
                broker.close()
            output.close()
            output.join_thread()
            for area in {area for area, _ in namespaces}:
                conn.execute(sql.SQL("DROP SCHEMA {} CASCADE").format(sql.Identifier(area)))


def test_notification_channels_are_isolated():
    schema = "notifications_" + uuid4().hex[:10]
    channels = [notification_channel("same", event, schema=schema, prefix=prefix)
                for prefix in ("a_", "b_") for event in ("enqueue", "ack", "results")]
    assert len(set(channels)) == 6
    with psycopg.connect("", autocommit=True) as listener, psycopg.connect("", autocommit=True) as sender:
        listener.execute(sql.SQL("LISTEN {}").format(sql.Identifier(channels[0])))
        sender.execute("SELECT pg_notify(%s, %s)", (channels[3], "foreign"))
        assert list(listener.notifies(timeout=0.02)) == []
        sender.execute("SELECT pg_notify(%s, %s)", (channels[0], "own"))
        assert [item.payload for item in listener.notifies(timeout=1, stop_after=1)] == ["own"]
