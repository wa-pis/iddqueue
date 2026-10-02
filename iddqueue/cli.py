import argparse
import bdb
import importlib.metadata
import json
import logging
import os
import pdb
import signal
import sys
import threading
from datetime import datetime
from textwrap import dedent
from uuid import UUID

from dramatiq import Message
from dramatiq.cli import LOGFORMAT, VERBOSITY
from dramatiq.common import q_name
from psycopg import sql
from psycopg.types.json import Jsonb

from .broker import QUERIES as BROKER_QUERIES
from .broker import PostgresBroker, message_lock, purge
from .cancellation import cancel, cancellation_status
from .control import is_paused, set_paused
from .history import list_attempts, purge_attempts
from .metrics import queue_statistics
from .scheduler import PostgresScheduler
from .schema import generate_init_sql, generate_upgrade_sql
from .utils import QueryManager, make_pool, transaction

logger = logging.getLogger(__name__)


# Function copied from distutils (now removed from Python), original code
# under MIT.
def strtobool(val: str) -> bool:
    """Convert a string representation of truth to true (1) or false (0).

    True values are 'y', 'yes', 't', 'true', 'on', and '1'; false values
    are 'n', 'no', 'f', 'false', 'off', and '0'.  Raises ValueError if
    'val' is anything else.
    """
    val = val.lower()
    if val in ("y", "yes", "t", "true", "on", "1"):
        return True
    elif val in ("n", "no", "f", "false", "off", "0"):
        return False
    else:
        raise ValueError(f"invalid truth value {val!r}")


def entrypoint():
    debug = strtobool(os.environ.get("DEBUG", "n"))
    level = logging.DEBUG if debug else logging.INFO
    logging.basicConfig(level=level, format=LOGFORMAT)

    try:
        exit(main())
    except (bdb.BdbQuit, KeyboardInterrupt):
        logger.info("Interrupted.")
    except Exception:
        logger.exception("Unhandled error:")
        if debug:
            pdb.post_mortem(sys.exc_info()[2])
        else:
            logger.error("Report this error to the IDDQueue project maintainer.")
    exit(1)


def main():
    parser = make_argument_parser()
    args = parser.parse_args()

    logging.getLogger().setLevel(VERBOSITY.get(args.verbose, logging.INFO))

    if not hasattr(args, "command"):
        logger.error("Missing command. See --help for usage.")
        return 1

    args.pool = make_pool(args.url, maxconn=1)
    try:
        try:
            with transaction(args.pool) as curs:
                curs.execute("SELECT 1")
        except Exception as e:
            logger.error("Failed to connect: %s.", e)
            return 1

        kw = dict(schema=args.schemaname, prefix=args.prefix)
        BROKER_QUERIES.build_queries(**kw)
        QUERIES.build_queries(**kw)
        return args.command(args)
    finally:
        args.pool.close()


def make_argument_parser():
    version = importlib.metadata.version("iddqueue")
    parser = argparse.ArgumentParser(
        prog="iddqueue",
        description="Maintainance utility for task-queue in Postgres.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument("--version", action="version", version=version)
    parser.add_argument(
        "--verbose",
        "-v",
        default=0,
        action="count",
        help="turn on verbose log output",
    )
    parser.add_argument(
        "-d",
        "--dsn",
        "--connstring",
        action="store",
        dest="url",
        default="",
        metavar="CONNSTRING",
        help="Postgres connection string.",
    )
    parser.add_argument(
        "--schemaname",
        action="store",
        dest="schemaname",
        default="dramatiq",
        metavar="SCHEMA",
        help=(
            'Alternative database schema for Dramatiq-pg DDL. Default is "%(default)s".'
        ),
    )
    parser.add_argument(
        "--prefix",
        action="store",
        dest="prefix",
        default="",
        metavar="PREFIX",
        help='Prefix for table name for message. Default is "%(default)s".',
    )

    subparsers = parser.add_subparsers()

    subparser = subparsers.add_parser("flush")
    subparser.set_defaults(command=flush_command)

    subparser = subparsers.add_parser("init")
    subparser.set_defaults(command=init_command)

    subparser = subparsers.add_parser("upgrade")
    subparser.set_defaults(command=upgrade_command)

    subparser = subparsers.add_parser("purge")
    subparser.set_defaults(command=purge_command)
    subparser.add_argument(
        "--maxage",
        dest="purge_maxage",
        default="30 days",
        help=dedent(
            """\
        Max age of done/rejected message to keep in queue. Format is Postgres
        interval. Default is %(default)r.
        """
        ),
    )

    subparser = subparsers.add_parser("recover")
    subparser.set_defaults(command=recover_command)
    subparser.add_argument(
        "--minage",
        dest="recover_minage",
        default="1 min",
        help=dedent(
            """\
        Max age of consumed message to requere. Format is Postgres
        interval. Default is %(default)r.
        """
        ),
    )

    subparser = subparsers.add_parser("stats")
    subparser.set_defaults(command=stats_command)
    subparser.add_argument("--queue")
    subparser.add_argument("--json", action="store_true")

    for name in ("pause", "resume", "queue-status"):
        control = subparsers.add_parser(name)
        control.add_argument("queue")
        control.set_defaults(command=control_command, control_operation=name)

    for name in ("cancel", "cancel-status"):
        cancellation = subparsers.add_parser(name)
        cancellation.add_argument("message_id", type=UUID)
        cancellation.set_defaults(command=cancellation_command, cancellation_operation=name)

    failed = subparsers.add_parser("failed")
    operations = failed.add_subparsers()
    listing = operations.add_parser("list")
    listing.set_defaults(command=failed_list_command)
    listing.add_argument("--queue")
    listing.add_argument("--actor")
    listing.add_argument("--limit", type=page_size, default=50)
    listing.add_argument("--after", type=UUID)
    show = operations.add_parser("show")
    show.set_defaults(command=failed_show_command)
    show.add_argument("message_id", type=UUID)
    show.add_argument("--payload", action="store_true")
    retry = subparsers.add_parser("retry")
    retry.set_defaults(command=retry_command)
    retry.add_argument("message_id", type=UUID)

    history = subparsers.add_parser("history")
    operations = history.add_subparsers()
    listing = operations.add_parser("list")
    listing.set_defaults(command=history_list_command)
    listing.add_argument("message_id", type=UUID)
    listing.add_argument("--limit", type=page_size, default=50)
    listing.add_argument("--after", type=UUID)
    retention = operations.add_parser("purge")
    retention.set_defaults(command=history_purge_command)
    retention.add_argument("--maxage", default="30 days")

    schedules = subparsers.add_parser("schedule").add_subparsers()
    create = schedules.add_parser("create")
    create.set_defaults(command=schedule_command, schedule_operation="create")
    create.add_argument("name")
    create.add_argument("actor")
    create.add_argument("--queue", default="default")
    create.add_argument("--interval-ms", type=positive_ms, required=True)
    create.add_argument("--start-at", type=datetime.fromisoformat)
    create.add_argument("--args", type=json.loads, default=[])
    create.add_argument("--kwargs", type=json.loads, default={})
    create.add_argument("--options", type=json.loads, default={})
    listing = schedules.add_parser("list")
    listing.set_defaults(command=schedule_command, schedule_operation="list")
    disable = schedules.add_parser("disable")
    disable.set_defaults(command=schedule_command, schedule_operation="disable")
    disable.add_argument("name")
    runner = subparsers.add_parser("scheduler")
    runner.set_defaults(command=scheduler_command)
    runner.add_argument("--poll-ms", type=positive_ms, default=1000)
    runner.add_argument("--once", action="store_true")

    return parser


def positive_ms(value):
    value = int(value)
    if value <= 0:
        raise argparse.ArgumentTypeError("milliseconds must be positive")
    return value


def _scheduler(args):
    return PostgresScheduler(PostgresBroker(pool=args.pool, schema=args.schemaname,
                                           prefix=args.prefix, results=False, middleware=[]))


def schedule_command(args):
    scheduler = _scheduler(args)
    if args.schedule_operation == "create":
        if not isinstance(args.args, list) or not isinstance(args.kwargs, dict) or not isinstance(args.options, dict):
            raise ValueError("args must be a JSON array; kwargs/options must be JSON objects")
        message = Message(args.queue, args.actor, tuple(args.args), args.kwargs, args.options)
        print(json.dumps(dict(schedule_id=scheduler.create(
            args.name, message, interval_ms=args.interval_ms, start_at=args.start_at))))
    elif args.schedule_operation == "list":
        print(json.dumps(scheduler.list()))
    else:
        found = scheduler.disable(args.name)
        print(json.dumps(dict(name=args.name, disabled=found)))
        return 0 if found else 1


def scheduler_command(args):
    scheduler = _scheduler(args)
    if args.once:
        print(json.dumps(dict(published=len(scheduler.tick()))))
        return
    stopped = threading.Event()
    previous = {sig: signal.signal(sig, lambda *_: stopped.set()) for sig in (signal.SIGTERM, signal.SIGINT)}
    try:
        while not stopped.is_set():
            count = len(scheduler.tick())
            if count:
                logger.info("Scheduler published %d occurrences.", count)
            stopped.wait(args.poll_ms / 1000)
    finally:
        for sig, handler in previous.items():
            signal.signal(sig, handler)


def history_list_command(args):
    print(json.dumps(list_attempts(args.pool, args.message_id, schema=args.schemaname,
                                   prefix=args.prefix, limit=args.limit, after=args.after)))


def history_purge_command(args):
    print(json.dumps(dict(deleted=purge_attempts(args.pool, args.maxage,
                                               schema=args.schemaname, prefix=args.prefix))))


def flush_command(args):
    with transaction(args.pool) as curs:
        curs.execute(QUERIES.FLUSH)
        flushed = curs.rowcount
    logger.info("Flushed %d messages.", flushed)


def purge_command(args):
    with transaction(args.pool) as curs:
        deleted = purge(curs, args.purge_maxage)
    logger.info("Deleted %d messages.", deleted)


def recover_command(args):
    with transaction(args.pool) as curs:
        curs.execute(QUERIES.RECOVER, (args.recover_minage,))
        recovered = curs.rowcount
    logger.info("Recovered %s messages.", recovered)


def init_command(args):
    with transaction(args.pool) as curs:
        curs.execute(generate_init_sql(args.schemaname, args.prefix))
    logger.info("Initialized database.")


def upgrade_command(args):
    with transaction(args.pool) as curs:
        curs.execute(generate_upgrade_sql(args.schemaname, args.prefix))
    logger.info("Upgraded database.")


def cancellation_command(args):
    operation = cancel if args.cancellation_operation == "cancel" else cancellation_status
    output = operation(args.pool, args.message_id, schema=args.schemaname, prefix=args.prefix)
    print(json.dumps(output))
    if output["state"] is None:
        return 1


def control_command(args):
    if args.control_operation != "queue-status":
        set_paused(args.pool, args.queue, args.control_operation == "pause",
                   schema=args.schemaname, prefix=args.prefix)
    print(json.dumps({"queue": q_name(args.queue),
                      "paused": is_paused(args.pool, args.queue,
                                          schema=args.schemaname, prefix=args.prefix)}))


def stats_command(args):
    if args.json or args.queue is not None:
        snapshots = queue_statistics(args.pool, schema=args.schemaname, prefix=args.prefix, queue=args.queue)
        print(json.dumps(snapshots))
        return
    with transaction(args.pool) as curs:
        curs.execute(QUERIES.STATS)
        stats = dict(curs.fetchall())

    for state in "queued", "consumed", "done", "rejected", "cancelled":
        print(f"{state}: {stats.get(state, 0)}")


def page_size(value):
    value = int(value)
    if not 1 <= value <= 1000:
        raise argparse.ArgumentTypeError("limit must be between 1 and 1000")
    return value


def _table(args):
    return sql.Identifier(args.schemaname, args.prefix + "queue")


def _summary(row):
    message_id, queue, state, actor, options = row
    options = options or {}
    failure = options.get("pg_failure")
    return dict(message_id=str(message_id), queue=queue, state=state,
                actor=actor, attempts=(failure or {}).get("attempt"),
                retries=options.get("retries", 0), error=failure)


def failed_list_command(args):
    with transaction(args.pool) as curs:
        curs.execute(sql.SQL(
            "SELECT message_id, queue_name, state::text, message->>'actor_name', "
            "message->'options' FROM {} WHERE state = 'rejected' "
            "AND (%s::text IS NULL OR queue_name = %s) "
            "AND (%s::text IS NULL OR message->>'actor_name' = %s) "
            "AND (%s::uuid IS NULL OR message_id > %s) ORDER BY message_id LIMIT %s"
        ).format(_table(args)), (args.queue, args.queue, args.actor, args.actor,
                               args.after, args.after, args.limit + 1))
        rows = curs.fetchall()
    page = rows[:args.limit]
    print(json.dumps(dict(items=[_summary(row) for row in page],
                          next_after=str(page[-1][0]) if len(rows) > args.limit else None)))


def failed_show_command(args):
    with transaction(args.pool) as curs:
        curs.execute(sql.SQL(
            "SELECT message_id, queue_name, state::text, message->>'actor_name', "
            "message->'options', message FROM {} WHERE message_id = %s AND state = 'rejected'"
        ).format(_table(args)), (args.message_id,))
        row = curs.fetchone()
    if row is None:
        logger.error("Rejected message not found: %s", args.message_id)
        return 1
    output = _summary(row[:5])
    if args.payload:
        output["message"] = row[5]
    print(json.dumps(output))


def retry_command(args):
    with transaction(args.pool) as curs:
        curs.execute(sql.SQL(
            "SELECT message FROM {} WHERE message_id = %s AND state = 'rejected' FOR UPDATE"
        ).format(_table(args)), (args.message_id,))
        row = curs.fetchone()
        if row is None:
            logger.error("Retry refused: message is missing or not rejected")
            return 1
        payload = row[0]
        message = Message(**payload)
        curs.execute("SELECT pg_try_advisory_xact_lock(%s)", (message_lock(message, schema=args.schemaname, prefix=args.prefix),))
        if not curs.fetchone()[0]:
            logger.error("Retry refused: worker still holds the message lock")
            return 1
        for key in ("retries", "traceback", "requeue_timestamp", "eta", "pg_failure"):
            payload["options"].pop(key, None)
        payload["queue_name"] = q_name(payload["queue_name"])
        curs.execute(sql.SQL(
            "UPDATE {} SET state = 'queued', message = %s, queue_name = %s, "
            "mtime = clock_timestamp(), result = NULL, result_ttl = NULL "
            "WHERE message_id = %s AND state = 'rejected'"
        ).format(_table(args)), (Jsonb(payload), payload["queue_name"], args.message_id))
        curs.execute("SELECT pg_notify(%s, %s)",
                     (BROKER_QUERIES.channel(payload["queue_name"], "enqueue"),
                      json.dumps({"message_id": str(args.message_id)})))
    print(json.dumps(dict(message_id=str(args.message_id), state="queued")))


QUERIES = QueryManager(
    dict(
        RECOVER=dedent(
            """\
    UPDATE {schema}.{tablename}
    SET state = 'queued', started = FALSE, mtime = clock_timestamp()
    WHERE state = 'consumed'
        AND mtime < NOW() - %s::interval;
    """
        ),
        STATS=dedent(
            """\
    SELECT "state", count(1)
    FROM {schema}.{tablename}
    GROUP BY "state";
    """
        ),
        FLUSH=dedent(
            """\
    DELETE FROM {schema}.{tablename}
    WHERE "state" IN ('queued', 'consumed');
    """
        ),
    )
)


if "__main__" == __name__:
    entrypoint()
