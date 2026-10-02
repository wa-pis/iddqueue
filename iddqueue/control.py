import logging

from dramatiq.common import dq_name, q_name
from dramatiq.middleware import Middleware, SkipMessage
from psycopg import sql

from .cancellation import notify_cancelled
from .utils import notification_channel, transaction


def table(schema, prefix):
    return sql.Identifier(schema, prefix + "queue_control")


def allow_start(cursor, queue, schema, prefix):
    control = table(schema, prefix)
    queue = q_name(queue)
    cursor.execute(sql.SQL(
        "INSERT INTO {} (queue_name) VALUES (%s) ON CONFLICT DO NOTHING"
    ).format(control), (queue,))
    # Shared locks allow concurrent starts; pause waits for these gates to commit.
    cursor.execute(sql.SQL(
        "SELECT paused FROM {} WHERE queue_name = %s FOR SHARE"
    ).format(control), (queue,))
    return not cursor.fetchone()[0]


def set_paused(pool, queue, paused, *, schema="dramatiq", prefix=""):
    queue = q_name(queue)
    with transaction(pool) as cursor:
        cursor.execute(sql.SQL("""
            INSERT INTO {} (queue_name, paused) VALUES (%s, %s)
            ON CONFLICT (queue_name) DO UPDATE SET paused = EXCLUDED.paused
        """).format(table(schema, prefix)), (queue, paused))
        if not paused:
            for name in (queue, dq_name(queue)):
                cursor.execute("SELECT pg_notify(%s, %s)", (
                    notification_channel(name, "enqueue", schema=schema, prefix=prefix),
                    '{"scan":true}',
                ))


def is_paused(pool, queue, *, schema="dramatiq", prefix=""):
    with transaction(pool) as cursor:
        cursor.execute(sql.SQL(
            "SELECT paused FROM {} WHERE queue_name = %s"
        ).format(table(schema, prefix)), (q_name(queue),))
        row = cursor.fetchone()
        return bool(row and row[0])


class QueueControl(Middleware):
    def before_process_message(self, broker, message):
        try:
            with transaction(broker.pool) as cursor:
                permitted = allow_start(cursor, message.queue_name,
                                        broker.queries.schema, broker.queries.prefix)
                if permitted:
                    table_name = sql.Identifier(broker.queries.schema, broker.queries.prefix + "queue")
                    cursor.execute(sql.SQL(
                        "SELECT state::text, cancel_requested FROM {} "
                        "WHERE message_id = %s FOR UPDATE"
                    ).format(table_name), (message.message_id,))
                    row = cursor.fetchone()
                    if row is None or row[0] == "cancelled" or row[1]:
                        if row and row[0] in ("queued", "consumed"):
                            cursor.execute(sql.SQL(
                                "UPDATE {} SET state = 'cancelled' WHERE message_id = %s"
                            ).format(table_name), (message.message_id,))
                            notify_cancelled(cursor, message.message_id,
                                             broker.queries.schema, broker.queries.prefix)
                        message._pg_cancelled = True
                    else:
                        cursor.execute(sql.SQL(
                            "UPDATE {} SET started = TRUE WHERE message_id = %s"
                        ).format(table_name), (message.message_id,))
        except SkipMessage:
            raise
        except Exception:
            # Dramatiq logs ordinary hook errors and continues: fail closed.
            logging.getLogger(__name__).exception("Queue start gate failed")
            permitted = False
        if getattr(message, "_pg_cancelled", False):
            raise SkipMessage("Task cancelled")
        if not permitted:
            message._pg_paused = True
            raise SkipMessage("Queue paused")
