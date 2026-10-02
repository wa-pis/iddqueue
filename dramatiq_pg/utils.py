import functools
import json
import logging
from contextlib import ExitStack, contextmanager
from urllib.parse import parse_qsl, urlparse

import tenacity
from dramatiq import Message, MessageProxy, get_encoder
from dramatiq.errors import BrokerConnectionError
from psycopg import InterfaceError, OperationalError, sql
from psycopg.conninfo import conninfo_to_dict, make_conninfo
from psycopg.errors import AdminShutdown
from psycopg_pool import ConnectionPool

logger = logging.getLogger(__name__)


DISCONNECT_ERRORS = (
    AdminShutdown,
    InterfaceError,
    OperationalError,
)


retry_pg = tenacity.retry(
    retry=tenacity.retry_if_exception_type(
        DISCONNECT_ERRORS + (BrokerConnectionError,)
    ),
    reraise=True,
    wait=tenacity.wait_random_exponential(multiplier=1, max=30),
    stop=tenacity.stop_after_attempt(10),
    before_sleep=tenacity.before_sleep_log(logger, logging.INFO),
)


def check_conn(conn):
    try:
        ConnectionPool.check_connection(conn)
    except DISCONNECT_ERRORS as e:
        if not conn.closed:
            logger.debug("Closing connexion due to error: %s", e)
            try:
                conn.close()
            except Exception as close_e:
                logger.debug("Failed to close connexion: %s", close_e)
        raise BrokerConnectionError(str(e)) from None
    return conn


@retry_pg
def getconn(pool):
    # Get a reliable connection to Postgres.
    if pool.closed:
        pool.open()
    conn = pool.getconn()
    try:
        check_conn(conn)
    except BrokerConnectionError:
        pool.putconn(conn)
        raise  # Let tenacity control retry.
    return conn


def make_pool(url, maxconn=16):
    if isinstance(url, str):
        if "://" in url:
            parts = urlparse(url)
            kwargs = dict(parse_qsl(parts.query))
            conninfo = url.split("?", 1)[0]
            pool_options = {
                key: kwargs.pop(key) for key in ("minconn", "maxconn") if key in kwargs
            }
            kwargs = conninfo_to_dict(conninfo, **kwargs)
            kwargs.update(pool_options)
        else:
            kwargs = conninfo_to_dict(url)
    else:
        kwargs = dict(url)

    maxconn = int(kwargs.pop("maxconn", maxconn))
    minconn = int(kwargs.pop("minconn", 0))
    kwargs.setdefault("application_name", "dramatiq-pg")
    kwargs.setdefault("keepalives", "1")
    kwargs.setdefault("keepalives_count", "2")
    kwargs.setdefault("keepalives_idle", "5")
    kwargs.setdefault("keepalives_interval", "2")
    return ConnectionPool(
        make_conninfo(**kwargs),
        min_size=minconn,
        max_size=maxconn,
        kwargs={"autocommit": True},
        open=False,
        check=ConnectionPool.check_connection,
    )


def raise_connection_error(fn):
    # Raises Dramatiq connection error on Psycopg error

    @functools.wraps(fn)
    def wrapper(*a, **kw):
        try:
            return fn(*a, **kw)
        except DISCONNECT_ERRORS as e:
            raise BrokerConnectionError(str(e))

    return wrapper


def quote_ident(raw):
    # Quote an SQL identifier, free from a connection object.
    return '"%s"' % raw.replace('"', '""')


def unlisten_all(conn):
    if not conn.closed:
        try:
            with conn.cursor() as cur:
                cur.execute("UNLISTEN *")
            # Discard notifications buffered before UNLISTEN.
            list(conn.notifies(timeout=0))
        except DISCONNECT_ERRORS:
            conn.close()


@contextmanager
def transaction(conn_or_pool, listen=None):
    with ExitStack() as defer:
        if hasattr(conn_or_pool, "getconn"):
            conn = getconn(conn_or_pool)
            defer.callback(conn_or_pool.putconn, conn)
        else:
            conn = conn_or_pool

        if listen:
            autocommit = conn.autocommit
            conn.autocommit = True
            try:
                with conn.cursor() as curs:
                    curs.execute(sql.SQL("LISTEN {}").format(sql.Identifier(listen)))
                    try:
                        yield curs
                    finally:
                        unlisten_all(conn)
            finally:
                if not conn.closed:
                    conn.autocommit = autocommit
        else:
            with conn.transaction(), conn.cursor() as curs:
                yield curs


def wait_for_notifies(conn, timeout=1):
    # Receive one batch without waiting for the entire timeout after a notify.
    return list(conn.notifies(timeout=timeout, stop_after=1))


class QueryManager:
    def __init__(self, queries, schema="dramatiq", prefix=""):
        self.queries = queries
        self.schema = schema
        self.prefix = prefix
        self.build_queries(schema, prefix)

    def build_queries(self, schema=None, prefix=None):
        schema = self.schema if schema is None else schema
        prefix = self.prefix if prefix is None else prefix
        self.schema, self.prefix = schema, prefix

        for name, query in self.queries.items():
            setattr(
                self,
                name,
                query.format(
                    schema=quote_ident(schema),
                    tablename=quote_ident(prefix + "queue"),
                ),
            )


def tidy4json(data):
    if isinstance(data, (Message, MessageProxy)):
        # Translate python data into decoded json.
        # Encode message using Dramatiq encoder. But immediatly decode it as
        # standard json to send native json to PostgreSQL.
        # e.g. date formating problem
        return json.loads(data.encode())
    else:
        return json.loads(get_encoder().encode(data))
