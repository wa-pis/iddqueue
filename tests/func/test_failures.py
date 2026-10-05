import json
import subprocess
import time
from concurrent.futures import ThreadPoolExecutor
from uuid import uuid4

import psycopg
import pytest
from dramatiq import Message
from dramatiq.results import ResultFailure
from psycopg import sql
from psycopg.types.json import Jsonb

from iddqueue import generate_init_sql
from iddqueue.broker import message_lock
from tests.func.actors import retryable


def cli(*args):
    return subprocess.run(["iddqueue", *map(str, args)], capture_output=True, text=True)


def rejected(conn, message_id, *, state="rejected"):
    message = Message(queue_name="offline", actor_name="private_actor", args=("secret",),
                      kwargs={}, options={"retries": 3, "traceback": "private trace", "eta": 10,
                                          "requeue_timestamp": 1,
                                          "pg_failure": {"type": "ValueError", "text": "bad", "attempt": 3}},
                      message_id=str(message_id))
    conn.execute("INSERT INTO dramatiq.queue (message_id, queue_name, state, message, result, result_ttl) VALUES (%s, %s, %s, %s, %s, now()+interval '1 day')",
                 (message_id, message.queue_name, state, Jsonb(message.asdict()), Jsonb({"old": True})))
    return message


def test_failed_pagination_and_payload():
    ids = sorted([uuid4() for _ in range(105)])
    with psycopg.connect("", autocommit=True) as conn:
        try:
            for message_id in ids:
                rejected(conn, message_id)
            out = cli("failed", "list", "--queue", "offline", "--actor", "private_actor", "--limit", 100)
            assert out.returncode == 0
            first = json.loads(out.stdout)
            assert len(first["items"]) == 100
            assert first["next_after"] == str(ids[99])
            second = json.loads(cli("failed", "list", "--queue", "offline", "--after", first["next_after"]).stdout)
            assert len(second["items"]) == 5
            assert second["next_after"] is None
            assert "secret" not in out.stdout and "private trace" not in out.stdout
            detail = cli("failed", "show", ids[0])
            assert "secret" not in detail.stdout
            assert json.loads(detail.stdout)["attempts"] == 3
            assert "secret" in cli("failed", "show", ids[0], "--payload").stdout
            assert cli("failed", "list", "--limit", 0).returncode != 0
            assert cli("failed", "show", uuid4()).returncode != 0
        finally:
            conn.execute("DELETE FROM dramatiq.queue WHERE message_id = ANY(%s)", (ids,))


def test_retry_guards_and_reset():
    ids = [uuid4() for _ in range(3)]
    with psycopg.connect("", autocommit=True) as conn:
        try:
            rejected(conn, ids[0], state="consumed")
            rejected(conn, ids[1], state="queued")
            message = rejected(conn, ids[2])
            for message_id in [ids[0], ids[1], uuid4()]:
                assert cli("retry", message_id).returncode == 1
            conn.execute("SELECT pg_advisory_lock(%s)", (message_lock(message),))
            assert cli("retry", ids[2]).returncode == 1
            conn.execute("SELECT pg_advisory_unlock_all()")
            conn.execute('LISTEN "dramatiq.offline.enqueue"')
            with ThreadPoolExecutor(2) as executor:
                outcomes = list(executor.map(lambda _: cli("retry", ids[2]).returncode, range(2)))
            assert sorted(outcomes) == [0, 1]
            notifications = list(conn.notifies(timeout=1, stop_after=1))
            assert json.loads(notifications[0].payload) == {"message_id": str(ids[2])}
            row = conn.execute("SELECT state, message, result, result_ttl FROM dramatiq.queue WHERE message_id = %s", (ids[2],)).fetchone()
            assert row[0] == "queued"
            assert row[1]["args"] == ["secret"]
            assert row[1]["options"] == {}
            assert row[2:] == (None, None)
            assert conn.execute("SELECT state FROM dramatiq.queue WHERE message_id = %s", (ids[0],)).fetchone()[0] == "consumed"
        finally:
            conn.execute("DELETE FROM dramatiq.queue WHERE message_id = ANY(%s)", (ids,))


@pytest.mark.timeout(20)
def test_real_failure_and_retry(restart_worker, witness):
    marker = str(uuid4())
    message = retryable.send(marker)
    with psycopg.connect("", autocommit=True) as conn:
        deadline = time.monotonic() + 8
        while time.monotonic() < deadline:
            row = conn.execute("SELECT state, message FROM dramatiq.queue WHERE message_id = %s", (message.message_id,)).fetchone()
            if row[1]["options"].get("retries") == 1:
                assert row[1]["options"]["pg_failure"]["attempt"] == 1
                break
            time.sleep(0.01)
        else:
            pytest.fail("Intermediate retry metadata not persisted")
        with pytest.raises(ResultFailure):
            message.get_result(block=True, timeout=8000)
        deadline = time.monotonic() + 5
        while time.monotonic() < deadline:
            out = cli("failed", "show", message.message_id)
            if out.returncode == 0:
                info = json.loads(out.stdout)
                assert info["attempts"] == 2
                assert info["error"]["type"] == "RuntimeError"
                assert info["error"]["time"]
                break
            time.sleep(0.05)
        else:
            pytest.fail("Final rejection not persisted")
        conn.execute("INSERT INTO functest.witness (payload) VALUES (%s)", (Jsonb({"ready": marker}),))
        deadline = time.monotonic() + 5
        while time.monotonic() < deadline:
            retry = cli("retry", message.message_id)
            if retry.returncode == 0:
                break
            assert "worker still holds" in retry.stderr
            time.sleep(0.05)
        else:
            pytest.fail("Worker did not release the rejected message lock")
        assert message.get_result(block=True, timeout=8000) == marker
        deadline = time.monotonic() + 5
        while time.monotonic() < deadline:
            state, payload = conn.execute("SELECT state, message FROM dramatiq.queue WHERE message_id = %s", (message.message_id,)).fetchone()
            if state == "done":
                assert "pg_failure" not in payload["options"]
                assert "retries" not in payload["options"]
                return
            time.sleep(0.01)
        pytest.fail("Successful retry was not acknowledged")


def test_custom_schema_cli():
    schema = "test_" + uuid4().hex
    with psycopg.connect("", autocommit=True) as conn:
        try:
            conn.execute(generate_init_sql(schema, "x_"))
            result = cli("--schemaname", schema, "--prefix", "x_", "failed", "list")
            assert result.returncode == 0
            assert json.loads(result.stdout) == {"items": [], "next_after": None}
        finally:
            conn.execute(sql.SQL("DROP SCHEMA {} CASCADE").format(sql.Identifier(schema)))


@pytest.mark.timeout(20)
def test_automatic_retry_success_clears_last_error(restart_worker, witness):
    marker = str(uuid4())
    message = retryable.send_with_options(args=(marker,), min_backoff=3000, max_backoff=3000)
    with psycopg.connect("", autocommit=True) as conn:
        deadline = time.monotonic() + 5
        while time.monotonic() < deadline:
            payload = conn.execute("SELECT message FROM dramatiq.queue WHERE message_id = %s", (message.message_id,)).fetchone()[0]
            if payload["options"].get("pg_failure"):
                conn.execute("INSERT INTO functest.witness (payload) VALUES (%s)", (Jsonb({"ready": marker}),))
                break
            time.sleep(0.01)
        else:
            pytest.fail("First failure was not persisted")
        assert message.get_result(block=True, timeout=8000) == marker
        deadline = time.monotonic() + 5
        while time.monotonic() < deadline:
            state, payload = conn.execute("SELECT state, message FROM dramatiq.queue WHERE message_id = %s", (message.message_id,)).fetchone()
            if state == "done":
                assert "pg_failure" not in payload["options"]
                assert payload["options"]["retries"] == 1
                return
            time.sleep(0.01)
        pytest.fail("Successful automatic retry was not acknowledged")
