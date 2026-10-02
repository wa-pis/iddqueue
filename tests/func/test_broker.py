import signal
import time
from datetime import datetime, timezone
from random import randint

import pytest

from example import failing, rejecting, sleeper, writer


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
        listener.wait(count)

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


@pytest.mark.timeout(8)
def test_retry(listener, pgconn, witness, worker):
    # Start listening for ack.
    with listener:
        failing.send(always=False, message="Testing retry")

        failed = True
        while failed:
            # Wait for ack of current try.
            listener.wait()

            # Check whether the task has been sucessful.
            with pgconn() as curs:
                curs.execute("SELECT * FROM functest.witness;")
            failed = 0 == curs.rowcount


@pytest.mark.timeout(4)
def test_nack(listener, pgconn, witness, worker):
    with listener:
        rejecting.send(message="Rejecting from func test.")
        listener.wait(1)

    with pgconn() as curs:
        curs.execute("SELECT payload FROM functest.witness LIMIT 1;")
        (payload,) = curs.fetchone()
    assert "Rejecting from func test." == payload["kwargs"]["message"]


@pytest.mark.timeout(8)
def test_delay(listener, pgconn, worker):
    with listener:
        queue_time = datetime.now(timezone.utc)
        writer.send("no delay")
        writer.send_with_options(args=("delayed",), delay=1000)
        listener.wait()
        immediate_delta = datetime.now(timezone.utc) - queue_time
        listener.wait()
        delayed_delta = datetime.now(timezone.utc) - queue_time

    assert immediate_delta.total_seconds() < 1
    assert delayed_delta.total_seconds() > 1

    with listener:
        queue_time = datetime.now(timezone.utc)
        # Dramatiq worker loops each second. Thus, delaying 2s ensure the
        # message wont be processed before SIGHUP.
        writer.send_with_options(args=("requeued",), delay=2000)
        # SIGHUP triggers requeue, restart and recover.
        worker.proc.send_signal(signal.SIGHUP)
        listener.wait()
        delayed_delta = datetime.now(timezone.utc) - queue_time

    assert delayed_delta.total_seconds() > 1


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
        listener.wait(1, timeout=30)


def test_crash(listener, worker):
    with listener:
        with worker.open_log() as fo:
            # Send a somewhat long message. Longer than dramatiq loop.
            sleeper.send(1.5)

            # Watch log for message reception.
            worker.watch_log(fo, "Received message sleeper(1.5)")

        # Kill *all* dramatiq processes.
        worker.crash()

        # Ensure that the message is not processed.
        with pytest.raises(listener.Timeout):
            listener.wait(1, timeout=2)


def test_recover(listener, restart_worker):
    # Now restart worker and ensure the message is processed.
    with listener:
        listener.wait(1, timeout=5)
