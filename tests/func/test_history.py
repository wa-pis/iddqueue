import json
import os
import subprocess
import time
from uuid import uuid4

import dramatiq
import psycopg
import pytest
from dramatiq.worker import Worker
from psycopg import sql

from iddqueue import PostgresBroker, generate_init_sql
from iddqueue.history import list_attempts, purge_attempts
from iddqueue.schema import generate_upgrade_sql
from tests.func.actors import saver

from .conftest import WorkerManager


@pytest.fixture
def area():
    schema = 'history"' + uuid4().hex[:10]
    prefix = 'jobs"_'
    with psycopg.connect("", autocommit=True) as conn:
        conn.execute(generate_init_sql(schema, prefix))
        conn.execute(generate_upgrade_sql(schema, prefix))
        conn.execute(generate_upgrade_sql(schema, prefix))
    broker = PostgresBroker(schema=schema, prefix=prefix, attempt_history=True, queue_control=True)
    try:
        yield broker, schema, prefix
    finally:
        broker.close()
        with psycopg.connect("", autocommit=True) as conn:
            conn.execute(sql.SQL("DROP SCHEMA {} CASCADE").format(sql.Identifier(schema)))


def history(area, message, **kw):
    broker, schema, prefix = area
    return list_attempts(broker.pool, message.message_id, schema=schema, prefix=prefix, **kw)


def wait_for(read, predicate):
    deadline = time.monotonic() + 8
    while time.monotonic() < deadline:
        value = read()
        if predicate(value):
            return value
        time.sleep(0.02)
    pytest.fail(f"Timed out: {value}")


def cli(area, *args):
    _, schema, prefix = area
    output = subprocess.check_output(["iddqueue", "--schemaname", schema, "--prefix", prefix,
                                      "history", *args], text=True)
    return json.loads(output)


def test_retry_history(area):
    broker, _, _ = area
    attempts = []

    @dramatiq.actor(broker=broker, queue_name="history", store_results=True,
                    max_retries=1, min_backoff=20, max_backoff=20)
    def operation(secret):
        attempts.append(1)
        if len(attempts) == 1:
            raise ValueError("x" * 3000)
        return secret

    worker = Worker(broker, worker_threads=1, worker_timeout=20)
    worker.start()
    try:
        message = operation.send("private payload")
        assert message.get_result(backend=broker.backend, block=True, timeout=5000) == "private payload"
        records = wait_for(lambda: history(area, message)["items"],
                           lambda items: len(items) == 2 and all(i["finished_at"] for i in items))
        assert {i["outcome"] for i in records} == {"failed", "successful"}
        failed = next(i for i in records if i["outcome"] == "failed")
        assert failed["error_type"] == "ValueError"
        assert len(failed["error_text"]) == 2000
        assert all(i["duration_ms"] >= 0 for i in records)
        assert "private payload" not in json.dumps(records)
        page = cli(area, "list", message.message_id, "--limit", "1")
        assert len(page["items"]) == 1 and page["next_after"]
        last = cli(area, "list", message.message_id, "--limit", "1", "--after", page["next_after"])
        assert len(last["items"]) == 1 and last["next_after"] is None
        assert last["items"][0]["attempt_id"] != page["items"][0]["attempt_id"]
        # Retention is independent of queue/results and preserves newer records.
        _, schema, prefix = area
        with psycopg.connect("", autocommit=True) as conn:
            conn.execute(sql.SQL("UPDATE {} SET started_at = now() - interval '40 days' WHERE attempt_id = %s")
                         .format(sql.Identifier(schema, prefix + "attempts")), (failed["attempt_id"],))
        assert cli(area, "purge", "--maxage", "30 days") == {"deleted": 1}
        assert len(history(area, message)["items"]) == 1
        assert message.get_result(backend=broker.backend) == "private payload"
        broker.pause_queue("history")
        pending = operation.send("queued")
        assert cli(area, "purge", "--maxage", "30 days") == {"deleted": 0}
        with psycopg.connect("", autocommit=True) as conn:
            assert conn.execute(sql.SQL("SELECT state::text FROM {} WHERE message_id = %s")
                                .format(sql.Identifier(schema, prefix + "queue")),
                                (pending.message_id,)).fetchone() == ("queued",)
    finally:
        worker.stop(timeout=5000)


def test_disabled_and_isolation(area):
    broker, schema, prefix = area
    other = PostgresBroker(schema=schema, prefix="other_", attempt_history=True)
    disabled = PostgresBroker(schema=schema, prefix=prefix)
    try:
        with psycopg.connect("", autocommit=True) as conn:
            # Init shares schema but has independent prefixed tables.
            conn.execute(generate_init_sql(schema, "other_"))
        @dramatiq.actor(broker=disabled, queue_name="disabled", store_results=True)
        def operation():
            return "done"

        worker = Worker(disabled, worker_threads=1, worker_timeout=20)
        worker.start()
        try:
            message = operation.send()
            assert message.get_result(backend=disabled.backend, block=True, timeout=5000) == "done"
        finally:
            worker.stop(timeout=5000)
        assert history(area, message)["items"] == []
        # Execute the same message ID in a second namespace with history enabled.
        other.declare_actor(operation)
        worker = Worker(other, worker_threads=1, worker_timeout=20)
        worker.start()
        try:
            other.enqueue(message)
            assert message.get_result(backend=other.backend, block=True, timeout=5000) == "done"
            wait_for(lambda: list_attempts(other.pool, message.message_id, schema=schema,
                                          prefix="other_")["items"],
                     lambda items: len(items) == 1 and items[0]["outcome"] == "successful")
        finally:
            worker.stop(timeout=5000)
        assert history(area, message)["items"] == []
        with pytest.raises(ValueError, match="positive"):
            purge_attempts(broker.pool, "-1 day", schema=schema, prefix=prefix)
        with pytest.raises(ValueError, match="limit"):
            history(area, message, limit=0)
    finally:
        disabled.close()
        other.close()


@pytest.mark.timeout(40)
def test_real_worker_crash():
    queue = "history-crash-" + uuid4().hex[:10]
    env = dict(os.environ, EXAMPLE_QUEUE=queue, EXAMPLE_ATTEMPT_HISTORY="1")
    worker = WorkerManager(name="history-crash", env=env)
    broker = dramatiq.get_broker()
    message = saver.message(wait=15, private="payload").copy(queue_name=queue)
    worker.start()
    try:
        broker.enqueue(message)
        first = wait_for(lambda: list_attempts(broker.pool, message.message_id)["items"], bool)[0]
        assert first["outcome"] == "incomplete" and first["finished_at"] is None
        worker.crash()
        worker.proc.wait(timeout=5)
        worker.stop()
        broker.enqueue(message.copy(kwargs={"wait": 0, "private": "payload"}))
        worker.start()
        assert message.get_result(block=True, timeout=8000) == {"private": "payload"}
        rows = wait_for(lambda: list_attempts(broker.pool, message.message_id)["items"],
                        lambda items: len(items) == 2 and any(i["outcome"] == "successful" for i in items))
        incomplete = next(i for i in rows if i["attempt_id"] == first["attempt_id"])
        assert incomplete == first
        assert "payload" not in json.dumps(rows)
    finally:
        worker.stop()
        with psycopg.connect("", autocommit=True) as conn:
            conn.execute("DELETE FROM dramatiq.attempts WHERE message_id = %s", (message.message_id,))
            conn.execute("DELETE FROM dramatiq.queue WHERE message_id = %s", (message.message_id,))
