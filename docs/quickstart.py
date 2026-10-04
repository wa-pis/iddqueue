"""Run against a dedicated PostgreSQL; create and remove an isolated schema."""

import os
from uuid import uuid4

import dramatiq
import psycopg
from psycopg import sql

from iddqueue import PostgresBroker, generate_init_sql

if os.environ.get("IDDQUEUE_TEST_DATABASE") != "dedicated":
    raise RuntimeError("Set IDDQUEUE_TEST_DATABASE=dedicated for the quickstart test")

schema = "quickstart_" + uuid4().hex
broker = PostgresBroker(schema=schema)
worker = None
with psycopg.connect("", autocommit=True) as connection:
    try:
        connection.execute(generate_init_sql(schema))
        tables = {row[0] for row in connection.execute(
            "SELECT tablename FROM pg_tables WHERE schemaname = %s", (schema,))}
        assert tables == {"queue", "coordination", "deduplication", "queue_control", "attempts", "schedules"}

        @dramatiq.actor(broker=broker, store_results=True)
        def add(left, right):
            return left + right

        message = add.send(2, 3)
        assert connection.execute(sql.SQL("SELECT count(*) FROM {} WHERE message_id = %s")
                                  .format(sql.Identifier(schema, "queue")), (message.message_id,)).fetchone()[0] == 1
        worker = dramatiq.Worker(broker, worker_threads=1, worker_timeout=100)
        worker.start()
        assert message.get_result(backend=broker.backend, block=True, timeout=10000) == 5
        print("Quickstart verified: six tables, enqueue, actor result=5")
    finally:
        try:
            if worker is not None:
                worker.stop()
                worker.join()
        finally:
            broker.close()
            connection.execute(sql.SQL("DROP SCHEMA IF EXISTS {} CASCADE").format(sql.Identifier(schema)))
assert connection.closed
print("Quickstart cleanup complete:", schema)
