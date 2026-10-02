import json
import os
import subprocess
import sys
import threading
import time
from datetime import datetime, timedelta, timezone
from uuid import uuid4

import dramatiq
import psycopg
import pytest
from dramatiq import Message
from dramatiq.worker import Worker
from psycopg import sql

from iddqueue import PostgresBroker, generate_init_sql, generate_upgrade_sql
from iddqueue.scheduler import PostgresScheduler


@pytest.fixture
def area():
    schema = 'scheduler"' + uuid4().hex[:10]
    prefix = 'jobs"_'
    with psycopg.connect("", autocommit=True) as conn:
        conn.execute(generate_init_sql(schema, prefix))
        conn.execute(generate_upgrade_sql(schema, prefix))
        conn.execute(generate_upgrade_sql(schema, prefix))
    broker = PostgresBroker(schema=schema, prefix=prefix, queue_control=True)
    try:
        yield PostgresScheduler(broker), schema, prefix
    finally:
        broker.close()
        with psycopg.connect("", autocommit=True) as conn:
            conn.execute(sql.SQL("DROP SCHEMA {} CASCADE").format(sql.Identifier(schema)))


def task(queue="scheduled"):
    return Message(queue, "unused", (), {"secret": "payload"}, {})


def wait_for(read, predicate=bool):
    deadline = time.monotonic() + 8
    while time.monotonic() < deadline:
        value = read()
        if predicate(value):
            return value
        time.sleep(0.02)
    pytest.fail(f"Timed out: {value}")


def rows(area, name):
    with psycopg.connect("", autocommit=True) as conn:
        return conn.execute(sql.SQL("SELECT count(*) FROM {}")
                            .format(sql.Identifier(area[1], area[2] + name))).fetchone()[0]


def test_coalesce_disable_and_utc(area):
    scheduler, _, _ = area
    with psycopg.connect("", autocommit=True) as conn:
        now = conn.execute("SELECT clock_timestamp()").fetchone()[0]
    due = now - timedelta(seconds=95)
    scheduler.create("missed", task(), interval_ms=10000, start_at=due.astimezone(timezone(timedelta(hours=4))))
    messages = scheduler.tick()
    assert len(messages) == 1 and messages[0].kwargs == {"secret": "payload"}
    listing = scheduler.list()[0]
    future = datetime.fromisoformat(listing["next_run"])
    assert future > now
    assert (future - due).total_seconds() == 100
    assert "payload" not in json.dumps(listing)
    assert scheduler.tick() == []
    assert scheduler.disable("missed") and scheduler.disable("missed")
    assert not scheduler.disable("missing")
    assert rows(area, "queue") == 1
    assert scheduler.list()[0]["enabled"] is False
    with psycopg.connect("", autocommit=True) as conn:
        conn.execute(sql.SQL("UPDATE {} SET next_run = clock_timestamp() - interval '1 day'")
                     .format(scheduler.table))
    assert scheduler.tick() == [] and rows(area, "queue") == 1


CHILD = '''
import json, sys, time
from pathlib import Path
from iddqueue import PostgresBroker
from iddqueue.scheduler import PostgresScheduler
schema, prefix, mode, ready, go = sys.argv[1:]
broker = PostgresBroker(schema=schema, prefix=prefix, results=False, middleware=[])
scheduler = PostgresScheduler(broker)
if mode == "before":
    original = broker.enqueue_in_transaction
    def blocked(*args, **kwargs):
        message = original(*args, **kwargs)
        Path(ready).touch()
        time.sleep(30)
        return message
    broker.enqueue_in_transaction = blocked
else:
    Path(ready).touch()
    while not Path(go).exists():
        time.sleep(0.01)
messages = scheduler.tick()
if mode == "after":
    Path(ready + ".committed").touch()
    time.sleep(30)
print(json.dumps([m.message_id for m in messages]), flush=True)
broker.close()
'''


def child(area, mode, ready, go):
    return subprocess.Popen([sys.executable, "-c", CHILD, area[1], area[2], mode, str(ready), str(go)],
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)


@pytest.mark.timeout(25)
def test_two_scheduler_processes(area, tmp_path):
    scheduler, _, _ = area
    scheduler.create("competing", task(), interval_ms=60000)
    go = tmp_path / "go"
    processes = [child(area, "normal", tmp_path / str(i), go) for i in range(2)]
    try:
        wait_for(lambda: all((tmp_path / str(i)).exists() for i in range(2)))
        go.touch()
        outputs = [proc.communicate(timeout=8) for proc in processes]
        assert all(proc.returncode == 0 for proc in processes), outputs
        assert sum(len(json.loads(out)) for out, _ in outputs) == 1
        assert rows(area, "queue") == rows(area, "deduplication") == 1
        assert scheduler.tick() == []
    finally:
        for proc in processes:
            if proc.poll() is None:
                proc.kill()
                proc.communicate()


@pytest.mark.parametrize("mode", ["before", "after"])
@pytest.mark.timeout(25)
def test_crash_commit_boundary(area, tmp_path, mode):
    scheduler, _, _ = area
    scheduler.create("crash", task(), interval_ms=60000)
    before = scheduler.list()[0]["next_run"]
    ready, go = tmp_path / "ready", tmp_path / "go"
    go.touch()
    proc = child(area, mode, ready, go)
    try:
        wait_for(lambda: (tmp_path / "ready.committed").exists() if mode == "after" else ready.exists())
        # A competing tick skips the locked row while the first process is in-flight.
        assert scheduler.tick() == []
        assert rows(area, "queue") == int(mode == "after")
        proc.kill()
        proc.communicate(timeout=5)
        messages = wait_for(scheduler.tick) if mode == "before" else scheduler.tick()
        assert len(messages) == int(mode == "before")
        assert rows(area, "queue") == rows(area, "deduplication") == 1
        assert scheduler.list()[0]["next_run"] != before
        assert scheduler.tick() == []
    finally:
        if proc.poll() is None:
            proc.kill()
            proc.communicate()


def test_paused_destination(area):
    scheduler, _, _ = area
    broker = scheduler.broker
    invoked = threading.Event()

    @dramatiq.actor(broker=broker, queue_name="paused", store_results=True)
    def operation():
        invoked.set()
        return "done"

    broker.pause_queue("paused")
    scheduler.create("paused", operation.message(), interval_ms=60000)
    message = scheduler.tick()[0]
    worker = Worker(broker, worker_threads=1, worker_timeout=20)
    worker.start()
    try:
        assert not invoked.wait(0.15)
        assert rows(area, "queue") == 1
        assert scheduler.tick() == []
        broker.resume_queue("paused")
        assert message.get_result(backend=broker.backend, block=True, timeout=5000) == "done"
        assert invoked.is_set()
    finally:
        worker.stop(timeout=5000)


def test_namespace_and_validation(area):
    scheduler, schema, _ = area
    other = PostgresBroker(schema=schema, prefix="other_", results=False, middleware=[])
    try:
        with psycopg.connect("", autocommit=True) as conn:
            conn.execute(generate_init_sql(schema, "other_"))
        alternate = PostgresScheduler(other)
        scheduler.create("same", task(), interval_ms=60000)
        alternate.create("same", task(), interval_ms=60000)
        assert len(scheduler.tick()) == len(alternate.tick()) == 1
        assert alternate.disable("same")
        assert scheduler.list()[0]["enabled"]
        for interval in [0, -1, True, 1.5]:
            with pytest.raises(ValueError, match="positive"):
                scheduler.create("invalid", task(), interval_ms=interval)
        with pytest.raises(ValueError, match="timezone"):
            scheduler.create("naive", task(), interval_ms=1000, start_at=datetime.now())
        with pytest.raises(ValueError, match="nonempty"):
            scheduler.create("", task(), interval_ms=1000)
        with pytest.raises(ValueError, match="limit"):
            scheduler.tick(limit=0)
    finally:
        other.close()


def command(area, *args):
    return ["iddqueue", "--schemaname", area[1], "--prefix", area[2], *args]


@pytest.mark.timeout(20)
def test_cli_and_clean_shutdown(area):
    output = subprocess.check_output(command(area, "schedule", "create", "cli", "unused",
                                            "--interval-ms", "60000", "--kwargs", '{"secret":"payload"}'), text=True)
    assert json.loads(output)["schedule_id"]
    listing = json.loads(subprocess.check_output(command(area, "schedule", "list"), text=True))
    assert listing[0]["actor"] == "unused" and "payload" not in json.dumps(listing)
    proc = subprocess.Popen(command(area, "scheduler", "--poll-ms", "20"),
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    try:
        wait_for(lambda: rows(area, "queue"))
        proc.terminate()
        _, err = proc.communicate(timeout=5)
        assert proc.returncode == 0, err
    finally:
        if proc.poll() is None:
            proc.kill()
            proc.communicate()
    output = subprocess.check_output(command(area, "scheduler", "--once"), text=True)
    assert json.loads(output) == {"published": 0}
    output = subprocess.check_output(command(area, "schedule", "disable", "cli"), text=True)
    assert json.loads(output) == {"name": "cli", "disabled": True}
    assert rows(area, "queue") == 1
    # No timezone/invalid JSON container must not create a schedule.
    for args in [("--start-at", "2026-10-03T00:00:00"), ("--args", '{}')]:
        bad = subprocess.run(command(area, "schedule", "create", "bad", "unused", "--interval-ms", "1", *args),
                             capture_output=True, text=True, env=dict(os.environ, DEBUG="n"))
        assert bad.returncode == 1
    assert len(area[0].list()) == 1
