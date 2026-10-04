import json
import logging
import time
from hashlib import sha256
from itertools import islice
from queue import Empty, Queue
from random import randint
from textwrap import dedent

from dramatiq.broker import Broker, Consumer, MessageProxy
from dramatiq.common import compute_backoff, current_millis, dq_name, q_name
from dramatiq.errors import BrokerConnectionError
from dramatiq.message import Message
from dramatiq.results import Results
from psycopg import Notify, sql
from psycopg.pq import TransactionStatus
from psycopg.types.json import Jsonb

from .cancellation import cancel, cancellation_status
from .control import QueueControl, allow_start, is_paused, set_paused
from .failures import FailureMetadata
from .history import AttemptHistory
from .results import PostgresBackend
from .utils import (
    QueryManager,
    check_conn,
    getconn,
    make_pool,
    raise_connection_error,
    retry_pg,
    storage_namespace,
    tidy4json,
    transaction,
    wait_for_notifies,
)

logger = logging.getLogger(__name__)


def purge(curs, max_age="30 days"):
    # Delete old messages. Returns deleted messages.

    curs.execute(QUERIES.PURGE, (max_age,))
    return curs.rowcount


class PostgresBroker(Broker):
    def __init__(
        self, *, pool=None, url="", results=True, schema=None, prefix=None, queue_control=False, attempt_history=False, **kw
    ):
        super().__init__(**kw)
        if pool is not None and url:
            raise ValueError("You can't set both pool and URL!")

        if pool is None:
            self.pool = make_pool(url)
        else:
            # Receive a pool object to have an I/O less __init__.
            self.pool = pool
        self._owns_pool = pool is None
        self.backend = None
        if results:
            self.backend = PostgresBackend(pool=self.pool, schema=schema, prefix=prefix)
            self.add_middleware(Results(backend=self.backend))

        self.add_middleware(FailureMetadata())
        self.queries = QueryManager(QUERIES.queries, schema or "dramatiq", prefix or "")
        if attempt_history:
            self.add_middleware(AttemptHistory())
        self.queue_control = queue_control
        if queue_control:
            self.add_middleware(QueueControl(), before=type(self.middleware[0]))

    def emit_after(self, signal, *args, **kwargs):
        # A deferred actor is not a terminal skip (Results must not store None).
        if signal == "skip_message" and (getattr(args[0], "_pg_paused", False) or getattr(args[0], "_pg_cancelled", False)):
            return
        return super().emit_after(signal, *args, **kwargs)

    def cancel(self, message_id):
        return cancel(self.pool, message_id, schema=self.queries.schema, prefix=self.queries.prefix)

    def cancellation_status(self, message_id):
        return cancellation_status(self.pool, message_id, schema=self.queries.schema, prefix=self.queries.prefix)

    def cancellation_requested(self, message_id):
        return self.cancellation_status(message_id)["requested"]

    def pause_queue(self, queue):
        set_paused(self.pool, queue, True, schema=self.queries.schema, prefix=self.queries.prefix)

    def resume_queue(self, queue):
        set_paused(self.pool, queue, False, schema=self.queries.schema, prefix=self.queries.prefix)

    def queue_is_paused(self, queue):
        return is_paused(self.pool, queue, schema=self.queries.schema, prefix=self.queries.prefix)


    def close(self):
        if self._owns_pool:
            self.pool.close()

    def consume(self, queue_name, prefetch=1, timeout=30000):
        return PostgresConsumer(
            pool=self.pool,
            queue_name=queue_name,
            prefetch=prefetch,
            timeout=timeout,
            queries=self.queries,
            queue_control=self.queue_control,
        )

    def declare_queue(self, queue_name):
        if queue_name not in self.queues:
            self.emit_before("declare_queue", queue_name)
            self.queues[queue_name] = True
            # Actually do nothing in Postgres since all queues are stored in
            # the same table.
            self.emit_after("declare_queue", queue_name)

            delayed_name = dq_name(queue_name)
            self.delay_queues.add(delayed_name)
            self.emit_after("declare_delay_queue", delayed_name)

    @retry_pg
    def enqueue(self, message, *, delay=None, deduplication_key=None, deduplication_ttl=None):
        if deduplication_key is not None or deduplication_ttl is not None:
            with transaction(self.pool) as curs:
                returned, published = self._enqueue_deduplicated(
                    curs, message, delay, deduplication_key, deduplication_ttl
                )
            if published:
                self.emit_after("enqueue", returned, delay)
            return returned
        message = self._prepare_enqueue(message, delay)
        with transaction(self.pool) as curs:
            self._write_enqueue(curs, message)
        self.emit_after("enqueue", message, delay)
        return message

    def enqueue_in_transaction(self, message, *, connection, delay=None, deduplication_key=None, deduplication_ttl=None):
        """Enqueue using the caller's active Psycopg transaction.

        The caller owns commit, rollback and the connection. Enqueue hooks
        describe the SQL operation, not the eventual transaction commit.
        Errors propagate without retrying the caller's transaction.
        """
        if connection.info.transaction_status != TransactionStatus.INTRANS:
            raise ValueError("enqueue_in_transaction requires an active transaction")
        if deduplication_key is not None or deduplication_ttl is not None:
            with transaction(connection) as curs:
                returned, published = self._enqueue_deduplicated(
                    curs, message, delay, deduplication_key, deduplication_ttl
                )
                if published:
                    self.emit_after("enqueue", returned, delay)
                return returned
        message = self._prepare_enqueue(message, delay)
        with connection.cursor() as curs:
            self._write_enqueue(curs, message)
        self.emit_after("enqueue", message, delay)
        return message

    def enqueue_many(self, messages, *, options=None):
        """Atomically enqueue up to 1000 messages with aligned enqueue options."""
        entries = self._batch_entries(messages, options)
        if not entries:
            return []
        with transaction(self.pool) as curs:
            returned, published = self._write_batch(curs, entries)
        for message, delay in published:
            self.emit_after("enqueue", message, delay)
        return returned

    def enqueue_many_in_transaction(self, messages, *, connection, options=None):
        """Use a savepoint; never commit or retry the caller's transaction."""
        if connection.info.transaction_status != TransactionStatus.INTRANS:
            raise ValueError("enqueue_many_in_transaction requires an active transaction")
        entries = self._batch_entries(messages, options)
        if not entries:
            return []
        with transaction(connection) as curs:
            returned, published = self._write_batch(curs, entries)
            for message, delay in published:
                self.emit_after("enqueue", message, delay)
        return returned

    @staticmethod
    def _batch_entries(messages, options):
        messages = list(islice(messages, 1001))
        if len(messages) > 1000:
            raise ValueError("batch limit is 1000 messages")
        options = [{} for _ in messages] if options is None else list(islice(options, 1001))
        if len(options) != len(messages):
            raise ValueError("options must match messages")
        allowed = {"delay", "deduplication_key", "deduplication_ttl"}
        for option in options:
            if not isinstance(option, dict) or option.keys() - allowed:
                raise ValueError("invalid enqueue options")
        return list(zip(messages, options))

    def _write_batch(self, curs, entries):
        returned, published = [], []
        if all(o.get("deduplication_key") is None and o.get("deduplication_ttl") is None
               for _, o in entries):
            for message, option in entries:
                delay = option.get("delay")
                message = self._prepare_enqueue(message, delay)
                returned.append(message)
                published.append((message, delay))
            # Psycopg executemany pipelines the existing per-message SQL.
            curs.executemany(self.queries.ENQUEUE, [self._enqueue_params(m) for m in returned])
        else:
            for message, option in entries:
                delay = option.get("delay")
                if option.get("deduplication_key") is not None or option.get("deduplication_ttl") is not None:
                    message, inserted = self._enqueue_deduplicated(
                        curs, message, delay, option.get("deduplication_key"), option.get("deduplication_ttl"))
                else:
                    message = self._prepare_enqueue(message, delay)
                    self._write_enqueue(curs, message)
                    inserted = True
                returned.append(message)
                if inserted:
                    published.append((message, delay))
        return returned, published

    def _enqueue_deduplicated(self, curs, message, delay, key, ttl):
        if not isinstance(key, str) or not key:
            raise ValueError("deduplication_key must be a nonempty string")
        if type(ttl) is not int or ttl <= 0:
            raise ValueError("deduplication_ttl must be positive integer milliseconds")
        table = sql.Identifier(self.queries.schema, self.queries.prefix + "deduplication")
        queue = q_name(message.queue_name)
        curs.execute(sql.SQL("""
            INSERT INTO {} AS stored (queue_name, key, message_id, message, expires_at)
            VALUES (%s, %s, %s, %s, clock_timestamp() + %s * interval '1 millisecond')
            ON CONFLICT (queue_name, key) DO UPDATE SET
                message_id = EXCLUDED.message_id, message = EXCLUDED.message,
                expires_at = EXCLUDED.expires_at
            WHERE stored.expires_at <= clock_timestamp()
            RETURNING message_id
        """).format(table), (queue, key, message.message_id, Jsonb(tidy4json(message)), ttl))
        if curs.fetchone() is None:
            curs.execute(sql.SQL(
                "SELECT message FROM {} WHERE queue_name = %s AND key = %s"
            ).format(table), (queue, key))
            return Message.decode(json.dumps(curs.fetchone()[0]).encode()), False
        message = self._prepare_enqueue(message, delay)
        self._write_enqueue(curs, message)
        curs.execute(sql.SQL(
            "UPDATE {} SET message = %s WHERE queue_name = %s AND key = %s"
        ).format(table), (Jsonb(tidy4json(message)), queue, key))
        return message, True

    def _prepare_enqueue(self, message, delay):
        self.emit_before("enqueue", message, delay)
        if delay:
            message = message.copy(queue_name=dq_name(message.queue_name))
            message.options["eta"] = current_millis() + delay
        return message

    def _write_enqueue(self, curs, message):
        logger.debug(
            "Upserting %s in queue %s.", message.message_id, message.queue_name
        )
        curs.execute(self.queries.ENQUEUE, self._enqueue_params(message))

    def _enqueue_params(self, message):
        return (message.queue_name, message.message_id, Jsonb(tidy4json(message)),
                self.queries.channel(message.queue_name, "enqueue"), message.message_id)



class PostgresConsumer(Consumer):
    def __init__(self, *, pool, queue_name, prefetch, timeout, queries=None, queue_control=False, **kw):
        self.queries = queries or QUERIES
        self.queue_control = queue_control
        self._consume_conn = None
        self._listen_conn = None
        self.notifies = []
        self.pool = pool
        self.queue_name = queue_name
        self.timeout = timeout / 1000
        self.unlock_q = Queue()
        self.in_processing = set()
        self.prefetch = prefetch
        self.misses = 0

    @raise_connection_error
    def __next__(self):
        # This function is executed each second.

        # First, open connexion and fetch missed notifies from table.
        if self._listen_conn is None:
            # Before reading from LISTEN, scan queue for missed messages.
            self.notifies = self.fetch_pending_notifies()
            logger.debug(
                "Found %s pending messages in queue %s.",
                len(self.notifies),
                self.queue_name,
            )

        self.purge_locks()

        processing = len(self.in_processing)
        if processing >= self.prefetch:
            # Wait and don't consume the message, other worker will be faster
            self.misses, backoff_ms = compute_backoff(self.misses, max_backoff=1000)
            logger.debug(
                f"Too many messages in processing: {processing} sleeping {backoff_ms}"
            )
            time.sleep(backoff_ms / 1000)
            return None

        if not self.notifies:
            # Then, fetch notifies from Pg connexion.
            self.poll_for_notify()

        if not self.notifies and not randint(0, 300):
            # If notifies are consumed, randomly poll for crashed messages.
            # Since we're called each second, this condition limits polling to
            # one SELECT every five minutes of inactivity.
            self.notifies[:] = self.fetch_pending_notifies()

        # If we have some notifies, loop to find one todo.
        while self.notifies:
            notify = self.notifies.pop(0)
            payload = json.loads(notify.payload)
            if payload.get("scan"):
                self.notifies += self.fetch_pending_notifies()
                continue
            # Legacy full payloads are hints too; claim returns durable data.
            message = Message(self.queue_name, "", (), {}, {}, message_id=payload["message_id"])
            claimed = self.consume_one(message)
            if claimed:
                self.in_processing.add(claimed.message_id)
                return MessageProxy(claimed)
            else:
                logger.debug(
                    "Message %s already consumed. Skipping.",
                    message.message_id,
                )

        # No message to process. Let's clean locks.
        self.purge_locks()

        # We have nothing to do, let's see if the queue needs some cleaning.
        self.auto_purge()

    @raise_connection_error
    def ack(self, message):
        # This function is executed in worker thread!
        if getattr(message, "_pg_cancelled", False):
            self.unlock_q.put_nowait(message)
            self.in_processing.remove(message.message_id)
            return
        if getattr(message, "_pg_paused", False):
            with transaction(self.pool) as curs:
                curs.execute(self.queries.DEFER_PAUSED, (message.message_id, message.queue_name))
            self.unlock_q.put_nowait(message)
            self.in_processing.remove(message.message_id)
            return

        with transaction(self.pool) as curs:
            channel = self.queries.channel(message.queue_name, "ack")
            payload = tidy4json(message)
            logger.debug("Notifying %s for ACK %s.", channel, message.message_id)
            # dramatiq always ack a message, even if it has been requeued by
            # the Retries middleware. Thus, only update message in state
            # `consumed`.
            curs.execute(
                self.queries.ACK,
                (
                    Jsonb(payload),
                    message.message_id,
                    message.queue_name,
                    channel,
                    message.message_id,
                ),
            )
        self.unlock_q.put_nowait(message)
        self.in_processing.remove(message.message_id)

    @raise_connection_error
    def auto_purge(self):
        # Automatically purge messages every 100k iteration. Dramatiq defaults
        # to 1s. This mean about 1 purge for 28h idle.
        if randint(0, 100_000):
            return
        logger.debug("Randomly triggering garbage collector.")
        with transaction(self._consume_conn) as curs:
            curs.execute(self.queries.PURGE, ("30 days",))
            deleted = curs.rowcount
        logger.info("Purged %d messages in all queues.", deleted)

    def close(self):
        # Closing the sessions releases subscriptions and all advisory locks,
        # including after a disconnect or a partially completed shutdown.
        for name in ("_listen_conn", "_consume_conn"):
            conn = getattr(self, name)
            if conn is not None:
                conn.close()
                self.pool.putconn(conn)
                setattr(self, name, None)

    def get_consume_conn(self):
        # Ensure connection used for message consumption is steady.
        if self._consume_conn is not None:
            try:
                check_conn(self._consume_conn)
            except BrokerConnectionError:
                logger.info("Connection closed. Reconnecting...")
                self.pool.putconn(self._consume_conn)
                self._consume_conn = None

        if self._consume_conn is None:
            logger.debug("Asking new connection for message consumption.")
            self._consume_conn = getconn(self.pool)

        return self._consume_conn

    @raise_connection_error
    def get_listen_conn(self):
        # Opens listening connection with proper configuration.
        if self._listen_conn is not None:
            try:
                return check_conn(self._listen_conn)
            except BrokerConnectionError:
                logger.info("Connection closed. Reconnecting...")
                self.pool.putconn(self._listen_conn)
                self._listen_conn = None

        self._listen_conn = conn = getconn(self.pool)
        # This is for NOTIFY consistency, according to Psycopg documentation.
        conn.autocommit = True
        channel = sql.Identifier(self.queries.channel(self.queue_name, "enqueue"))
        with conn.cursor() as curs:
            logger.debug("Listening on channel %s.", channel)
            curs.execute(sql.SQL("LISTEN {}").format(channel))
        return self._listen_conn

    @raise_connection_error
    def consume_one(self, message):
        if message.message_id in self.in_processing:
            logger.debug("%s already consumed by self.", message.message_id)
            return

        # Race to process message.
        with transaction(self.get_consume_conn()) as curs:
            if self.queue_control and not allow_start(
                curs, self.queue_name, self.queries.schema, self.queries.prefix
            ):
                return False
            lock = message_lock(message.copy(queue_name=self.queue_name), schema=self.queries.schema, prefix=self.queries.prefix)
            curs.execute(self.queries.CONSUME_ONE, (message.message_id, self.queue_name, lock))
            row = curs.fetchone()
            # If no row was updated, this mean another worker has consumed it.
            successfully_consumed = row is not None

            if successfully_consumed:
                logger.info("Consumed %s@%s.", message.message_id, message.queue_name)
            else:
                # Release the lock in case lock acquisition took place before
                # other clauses failed.
                curs.execute(self.queries.RELEASE_ONE, (lock,))

            return Message.decode(row[0].encode()) if successfully_consumed else None

    @raise_connection_error
    def nack(self, message):
        # This function is executed in worker thread.

        with transaction(self.pool) as curs:
            # Use the same channel as ack. Actually means done.
            channel = self.queries.channel(message.queue_name, "ack")
            logger.debug("Notifying %s for NACK %s.", channel, message.message_id)
            payload = tidy4json(message)
            curs.execute(
                self.queries.NACK,
                (
                    Jsonb(payload),
                    message.message_id,
                    message.queue_name,
                    channel,
                    message.message_id,
                ),
            )
        self.unlock_q.put_nowait(message)
        self.in_processing.remove(message.message_id)

    @raise_connection_error
    def fetch_pending_notifies(self):
        logger.debug("Polling for lost messages in %s.", self.queue_name)
        # Get or open connection.
        conn = self.get_listen_conn()
        # We may have received a notify between LISTEN and SELECT of pending
        # messages. That's not a problem because we are able to skip spurious
        # notifies.
        channel = self.queries.channel(self.queue_name, "enqueue")
        with transaction(conn) as curs:
            curs.execute(self.queries.FETCH_PENDING, (self.queue_name,))
            return [Notify(pid=0, channel=channel, payload=r[0]) for r in curs]

    @raise_connection_error
    def poll_for_notify(self):
        self.notifies += wait_for_notifies(self.get_listen_conn(), self.timeout)

    @raise_connection_error
    def purge_locks(self):
        with transaction(self.get_consume_conn()) as curs:
            while True:
                try:
                    message = self.unlock_q.get(block=False)
                except Empty:
                    return
                lock = message_lock(message, schema=self.queries.schema, prefix=self.queries.prefix)
                logger.debug(
                    "Unlocking %s@%s (%s).",
                    message.message_id,
                    message.queue_name,
                    lock,
                )
                curs.execute(
                    self.queries.RELEASE_ONE,
                    (lock,),
                )
                # Retry may be queued while this attempt still holds its lock.
                curs.execute(
                    self.queries.NOTIFY_UNLOCKED,
                    (self.queries.channel(message.queue_name, "enqueue"),
                     message.message_id, message.message_id, message.queue_name),
                )
                self.unlock_q.task_done()

    @raise_connection_error
    def requeue(self, messages):
        messages = list(messages)
        if not len(messages):
            return

        logger.debug("Batch update of messages for requeue.")
        with transaction(self.get_consume_conn()) as curs:
            curs.execute(self.queries.REQUEUE, ([str(m.message_id) for m in messages],))
            # We don't bother about locks, because requeue occurs on worker
            # stop.


_max_positive_int = 2**63


def message_lock(message, *, schema="dramatiq", prefix=""):
    # create sha256 hash from input and create a 64 bit int from it, using
    # 16 hex char. any 16 char range is ok. it takes the center ones
    global_id = message.queue_name + str(message.message_id)
    if schema != "dramatiq" or prefix:
        global_id = storage_namespace(schema, prefix) + global_id
    hex = sha256(global_id.encode("utf-8")).hexdigest()
    unsigned = int(hex[24:40], 16)
    # PostgreSQL lock is a signed int on 64 bytes. Shift unsigned value from
    # interval [0..2**64] to interval [-2**63..2**63].
    return unsigned - _max_positive_int


QUERIES = QueryManager(
    dict(
        ACK=dedent(
            """\
        WITH updated AS (
            UPDATE {schema}.{tablename}
                SET "state" = 'done', message = %s
            WHERE message_id = %s
                AND queue_name = %s
                AND state = 'consumed'
            RETURNING message
        )
        SELECT
            pg_notify(%s,
                jsonb_build_object('message_id', %s::text)::text
            )
        FROM updated;
        """
        ),
        DEFER_PAUSED="""
        UPDATE {schema}.{tablename} SET state = 'queued'
        WHERE message_id = %s AND queue_name = %s AND state = 'consumed';
        """,
        CONSUME_ONE=dedent(
            """\
        UPDATE {schema}.{tablename}
            SET "state" = 'consumed', started = FALSE,
                mtime = NOW()
            WHERE message_id = %s AND queue_name = %s
            AND state IN ('queued', 'consumed')
            AND pg_try_advisory_lock(%s)
            RETURNING message::text;
        """
        ),
        NOTIFY_UNLOCKED="""
        SELECT pg_notify(%s, jsonb_build_object('message_id', %s::text)::text)
        FROM {schema}.{tablename}
        WHERE message_id = %s AND queue_name = %s AND state = 'queued';
        """,
        RELEASE_ONE="""SELECT pg_advisory_unlock(%s)""",
        ENQUEUE=dedent(
            """\
        WITH enqueued AS (
            INSERT INTO {schema}.{tablename}
            (queue_name, message_id, "state", message)
            VALUES (%s, %s, 'queued', %s)
            ON CONFLICT (message_id)
                DO UPDATE SET
                    "state" = 'queued', started = FALSE,
                    message = EXCLUDED.message,
                    mtime = clock_timestamp(),
                    queue_name = EXCLUDED.queue_name
            WHERE {schema}.{tablename}.state <> 'cancelled'
            RETURNING queue_name, message
        )
        SELECT
            pg_notify(%s,
                jsonb_build_object('message_id', %s::text)::text
            )
        FROM enqueued;
        """
        ),  # noqa
        FETCH_PENDING=dedent(
            """\
        SELECT message::text
            FROM {schema}.{tablename}
            WHERE state IN ('queued', 'consumed')
            AND queue_name = %s;
        """
        ),
        NACK=dedent(
            """\
        WITH updated AS (
            UPDATE {schema}.{tablename}
                SET "state" = 'rejected', message = %s
            WHERE message_id = %s
                AND queue_name = %s
                AND state IN ('queued', 'consumed')
            RETURNING message
        )
        SELECT
            pg_notify(%s,
                jsonb_build_object('message_id', %s::text)::text
            )
        FROM updated;
        """
        ),
        PURGE=dedent(
            """\
        DELETE FROM {schema}.{tablename}
        WHERE "state" IN ('done', 'rejected', 'cancelled')
        AND mtime <= (NOW() - %s::interval);
        """
        ),
        REQUEUE=dedent(
            """\
        UPDATE {schema}.{tablename}
            SET state = 'queued', started = FALSE, mtime = clock_timestamp()
        WHERE message_id = ANY(%s::uuid[]) AND state IN ('queued', 'consumed');
        """
        ),
    )
)
