import argparse
import bdb
import importlib.metadata
import json
import logging
import os
import pdb
import sys
from textwrap import dedent
from uuid import UUID

from dramatiq import Message
from dramatiq.cli import LOGFORMAT, VERBOSITY
from dramatiq.common import q_name
from psycopg import sql
from psycopg.types.json import Jsonb

from .broker import QUERIES as BROKER_QUERIES
from .broker import message_lock, purge
from .metrics import queue_statistics
from .schema import generate_init_sql
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
            logger.error(
                "Please file an issue at "
                "https://gitlab.com/dalibo/dramatiq-pg/issues/new with full "
                "log.",
            )
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
    version = importlib.metadata.version("dramatiq-pg")
    parser = argparse.ArgumentParser(
        prog="dramatiq-pg",
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

    return parser


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


def stats_command(args):
    if args.json or args.queue is not None:
        snapshots = queue_statistics(args.pool, schema=args.schemaname, prefix=args.prefix, queue=args.queue)
        print(json.dumps(snapshots))
        return
    with transaction(args.pool) as curs:
        curs.execute(QUERIES.STATS)
        stats = dict(curs.fetchall())

    for state in "queued", "consumed", "done", "rejected":
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
        curs.execute("SELECT pg_try_advisory_xact_lock(%s)", (message_lock(message),))
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
                     ("dramatiq." + payload["queue_name"] + ".enqueue",
                      json.dumps({"message_id": str(args.message_id)})))
    print(json.dumps(dict(message_id=str(args.message_id), state="queued")))


QUERIES = QueryManager(
    dict(
        RECOVER=dedent(
            """\
    UPDATE {schema}.{tablename}
    SET state = 'queued', mtime = clock_timestamp()
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
