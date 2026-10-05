"""Actors used by functional tests and their separate Dramatiq workers."""

import asyncio
import logging
import os
import random
import time

import dramatiq.results
from dramatiq.middleware import AsyncIO, GroupCallbacks, Shutdown
from psycopg.types.json import Jsonb

import iddqueue
from iddqueue.utils import make_pool

logger = logging.getLogger(__name__)
# Test actors share the dedicated PostgreSQL configured through PG* variables.
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
