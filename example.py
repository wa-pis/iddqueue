#!/usr/bin/env python
#
#       E X A M P L E
#
#
# This example script is tested on CI. Testing code is in tests/func/. example
# is configured using PG* envvars, .pgpass and pg_service.conf file, like psql.
#
# The failing task can raise randomly error. This is helpful to check retrying
# a task until it succeed. You can seed random with an int SEED env var.
# 1550768028 is a known SEED to trigger exceptions at least once.
#
# The writer tasks inserts its arguments in functests.witness table as declared
# in tests/func/schema.sql.
#
# To run workers:
#
#     SEED=xx dramatiq --verbose -p 2 -t 2 example
#
# You can add `--watch .` in the above dramatiq command to prevent you from
# manually restarting when modifying files, but it may also cause dramatiq
# to restart inappropriately, fetching messages from db instead of receiving
# notification.
#
# To produce messages:
#
#     python example.py

import asyncio
import json
import logging
import os
import pdb
import random
import sys
import time

import dramatiq.results
from dramatiq.middleware import AsyncIO, GroupCallbacks, Shutdown
from psycopg.types.json import Jsonb

import iddqueue
from iddqueue.utils import make_pool

logger = logging.getLogger(__name__)
# Empty connstring let's you configure psycopg using PG* env vars.
pool = make_pool("application_name=iddqueue")
# PostgresBroker accepts either pool= or url=. URL is a libpq connstring.
# PostgresBroker creates a ConnectionPool from URL, swallowing minconn
# and maxconn query argument.
dramatiq.set_broker(iddqueue.PostgresBroker(pool=pool, queue_control=bool(os.environ.get("EXAMPLE_QUEUE_CONTROL")), attempt_history=bool(os.environ.get("EXAMPLE_ATTEMPT_HISTORY"))))
dramatiq.get_broker().add_middleware(AsyncIO())
if os.environ.get("EXAMPLE_PROMETHEUS"):
    from dramatiq.middleware.prometheus import Prometheus

    dramatiq.get_broker().add_middleware(Prometheus())
dramatiq.get_broker().add_middleware(
    GroupCallbacks(iddqueue.PostgresRateLimiterBackend(pool=pool))
)


seed = int(os.environ.get("SEED", int(time.time())))
random.seed(seed)


@dramatiq.actor(store_results=True, queue_name=os.environ.get("EXAMPLE_QUEUE", "default"))
def saver(*, wait=0, **data):
    time.sleep(wait)
    logger.debug("Returning %.60s.", data)
    return data


@dramatiq.actor
def sleeper(param):
    time.sleep(param)


@dramatiq.actor
def writer(*args, **kwargs):
    conn = iddqueue.utils.getconn(pool)
    insert = (
        "INSERT INTO functest.witness (payload) VALUES (%s::jsonb);",
        (Jsonb(dict(args=args, kwargs=kwargs)),),
    )
    try:
        with conn.transaction():
            with conn.cursor() as curs:
                logger.info("Inserting args in witness table.")
                curs.execute(*insert)
    finally:
        pool.putconn(conn)


# Set minimal value for max_backoff to avoid waiting 30days when running func
# tests on CI.
@dramatiq.actor(max_backoff=100, queue_name=os.environ.get("EXAMPLE_QUEUE", "default"))
def failing(always=True, message="Forged failure", wait=0):
    time.sleep(wait)
    if always or random.randint(0, 1):
        raise Exception(message)
    else:
        logger.info("Not failing (%s).", message)
    writer(message=message, notice="Did not failed.")


@dramatiq.actor(max_retries=0)
def rejecting(message="Rejecting"):
    writer(message=message)
    raise Exception(message)



@dramatiq.actor(store_results=True, max_retries=0)
def scale(value, factor=2, *, fail=False):
    if fail:
        raise ValueError("pipeline failed")
    return value * factor


@dramatiq.actor(store_results=True, max_retries=0)
async def async_value(value, *, fail=False):
    await asyncio.sleep(0.01)
    if fail:
        raise ValueError("async failed")
    return value


@dramatiq.actor(store_results=True)
def execution_time():
    return time.time()


@dramatiq.actor(store_results=True, max_retries=1, min_backoff=500, max_backoff=500)
def retryable(marker):
    conn = iddqueue.utils.getconn(pool)
    try:
        with conn.transaction(), conn.cursor() as cursor:
            cursor.execute("SELECT 1 FROM functest.witness WHERE payload->>'ready' = %s", (marker,))
            ready = cursor.fetchone() is not None
    finally:
        pool.putconn(conn)
    if not ready:
        raise RuntimeError("dependency is not ready")
    return marker


@dramatiq.actor(store_results=True, max_retries=0, notify_shutdown=True,
                queue_name=os.environ.get("EXAMPLE_QUEUE", "default"))
def shutdown_probe(marker):
    try:
        with iddqueue.utils.transaction(pool) as cursor:
            cursor.execute("INSERT INTO functest.witness (payload) VALUES (%s)",
                           (Jsonb({"shutdown_started": marker}),))
        deadline = time.monotonic() + 15
        while time.monotonic() < deadline:
            time.sleep(0.01)
        return "not interrupted"
    except Shutdown:
        with iddqueue.utils.transaction(pool) as cursor:
            cursor.execute("INSERT INTO functest.witness (payload) VALUES (%s)",
                           (Jsonb({"shutdown_cleanup": marker}),))
        return "shutdown"


def main():
    message = saver.send(wait=random.randint(0, 10), message="Saved.")
    for _ in range(10):
        sleeper.send(2)
        writer.send("toto", named="titi")
        failing.send(always=False)
        d = random.randint(4, 10) * 1000
        writer.send_with_options(args=("delayed",), delay=d)

    long_message = writer.send(long="a" * 7810)
    assert len(json.dumps(json.loads(long_message.encode()))) >= 8000
    writer.send("very", long="message" * 8000)
    rejecting.send()
    message.get_result(block=True, timeout=20_000)
    logger.debug("Got result from %s.", message.message_id)


if "__main__" == __name__:
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(levelname)1.1s: %(message)s",
    )
    logger.info("Random seed is %s.", seed)

    try:
        exit(main())
    except (pdb.bdb.BdbQuit, KeyboardInterrupt):
        logger.info("Interrupted.")
    except Exception:
        logger.exception("Unhandled error:")
        if sys.stdout.isatty():
            logger.debug("Dropping in debugger.")
            pdb.post_mortem(sys.exc_info()[2])

    exit(os.EX_SOFTWARE)
elif logging.getLogger().handlers:
    # Log for dramatiq worker process.
    logger.info("Random seed is %s.", seed)
