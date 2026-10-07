import json
import signal
import time
from random import randint
from uuid import uuid4

import pytest
from dramatiq.results import ResultTimeout

from tests.func.actors import crash_probe, execution_time, rejecting, retryable, writer


def test_listener_matches_task(listener, pgconn):
    expected = str(uuid4())
    with listener:
        with pgconn() as curs:
            for message_id in [str(uuid4()), expected]:
                curs.execute("SELECT pg_notify('dramatiq.default.ack', %s)",
                             (json.dumps({"message_id": message_id}),))
        received = listener.wait(message_ids=[expected])
        assert [json.loads(n.payload)["message_id"] for n in received] == [expected]


@pytest.mark.timeout(12)
def test_massive(listener, pgconn, witness, worker):
    count = 64

    # Start listening for ack.
    with listener:
        messages = []  # For debugging.
        # Then queue <count> random messages.
        for n in range(count):
            message = writer.send(
                randint(1, 10),
                message="Message #%d" % (n,),
            )
            messages.append(message)

        # Wait for *count* ack from workers.
        listener.wait(count, message_ids=[m.message_id for m in messages])

    # Ensure the witness table has effectively been updated.
    with pgconn() as curs:
        curs.execute("SELECT count(*) FROM functest.witness;")
        (witness_count,) = curs.fetchone()
    assert count == witness_count

    time.sleep(2)  # allow some time for clearing the locks

    with pgconn() as curs:
        curs.execute(
            """
        SELECT count(*) FROM pg_catalog.pg_locks WHERE locktype = 'advisory';
        """
        )
        (locks,) = curs.fetchone()
    assert locks == 0


@pytest.mark.timeout(30)
def test_retry(pgconn, witness, worker):
    marker = uuid4().hex
    message = retryable.send(marker)
    deadline = time.monotonic() + 8
    while time.monotonic() < deadline:
        with pgconn() as curs:
            curs.execute("SELECT message FROM dramatiq.queue WHERE message_id=%s", (message.message_id,))
            payload = curs.fetchone()[0]
        if payload["options"].get("pg_failure", {}).get("attempt") == 1:
            break
        time.sleep(0.01)
    else:
        pytest.fail("Controlled first failure was not persisted")
    with pgconn() as curs:
        curs.execute("INSERT INTO functest.witness(payload) VALUES (jsonb_build_object('ready', %s::text))", (marker,))
    assert message.get_result(block=True, timeout=10000) == marker


@pytest.mark.timeout(4)
def test_nack(listener, pgconn, witness, worker):
    with listener:
        message = rejecting.send(message="Rejecting from func test.")
        listener.wait(1, message_ids=[message.message_id])

    with pgconn() as curs:
        curs.execute("SELECT payload FROM functest.witness LIMIT 1;")
        (payload,) = curs.fetchone()
    assert "Rejecting from func test." == payload["kwargs"]["message"]


@pytest.mark.timeout(30)
def test_delay(worker):
    immediate = execution_time.send()
    delayed = execution_time.send_with_options(delay=1000)
    assert immediate.get_result(block=True, timeout=10000) >= immediate.message_timestamp / 1000
    assert delayed.get_result(block=True, timeout=10000) >= delayed.options["eta"] / 1000
    requeued = execution_time.send_with_options(delay=2000)
    worker.proc.send_signal(signal.SIGHUP)
    assert requeued.get_result(block=True, timeout=10000) >= requeued.options["eta"] / 1000


def test_reconnect(listener, pgconn, worker):
    # First, kill all other connexions.
    with pgconn() as curs:
        curs.execute(
            """
        SELECT pg_terminate_backend(pid)
        FROM pg_stat_activity
        WHERE datid IS NOT NULL AND pid <> pg_backend_pid();
        """
        )

    # Start listening for ack.
    with listener:
        message = writer.send(
            randint(1, 10),
            message="Message after kill.",
        )
        message  # This is for pytest to dump message UUID in error logs.

        # Wait for *count* ack from workers.
        listener.wait(1, timeout=30, message_ids=[message.message_id])


@pytest.mark.timeout(20)
def test_crash(pgconn, witness, worker):
    marker = uuid4().hex
    worker.crash_message = crash_probe.send(marker)
    deadline = time.monotonic() + 8
    while time.monotonic() < deadline:
        with pgconn() as curs:
            curs.execute("SELECT 1 FROM functest.witness WHERE payload->>'crash_started'=%s", (marker,))
            if curs.fetchone():
                break
        time.sleep(0.02)
    else:
        pytest.fail("Crash actor never reached controlled gate")
    worker.crash()
    worker.proc.wait(timeout=5)
    with pytest.raises(ResultTimeout):
        worker.crash_message.get_result(block=True, timeout=2000)
    with pgconn() as curs:
        curs.execute("INSERT INTO functest.witness(payload) VALUES (jsonb_build_object('crash_ready', %s::text))",
                     (marker,))


def test_recover(worker, restart_worker):
    assert worker.crash_message.get_result(block=True, timeout=10000) == worker.crash_message.args[0]
