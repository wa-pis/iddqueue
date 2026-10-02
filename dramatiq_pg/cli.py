import argparse
import bdb
import importlib.metadata
import logging
import os
import pdb
import sys
from textwrap import dedent

from dramatiq.cli import LOGFORMAT, VERBOSITY

from .broker import QUERIES as BROKER_QUERIES
from .broker import purge
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
    with transaction(args.pool) as curs:
        curs.execute(QUERIES.STATS)
        stats = dict(curs.fetchall())

    for state in "queued", "consumed", "done", "rejected":
        print(f"{state}: {stats.get(state, 0)}")


QUERIES = QueryManager(
    dict(
        RECOVER=dedent(
            """\
    UPDATE {schema}.{tablename}
    SET state = 'queued'
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
