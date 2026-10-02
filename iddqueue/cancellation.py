from dramatiq.results import ResultFailure
from psycopg import sql

from .utils import notification_channel, transaction


class ResultCancelled(ResultFailure):
    """The task was cancelled before execution; retained until queue purge."""


def notify_cancelled(cursor, message_id, schema, prefix):
    cursor.execute("SELECT pg_notify(%s, %s)", (
        notification_channel(str(message_id), "results", schema=schema, prefix=prefix),
        str(message_id),
    ))


def cancel(pool, message_id, *, schema="dramatiq", prefix=""):
    table = sql.Identifier(schema, prefix + "queue")
    with transaction(pool) as cursor:
        cursor.execute(sql.SQL(
            "SELECT state::text, started FROM {} WHERE message_id = %s FOR UPDATE"
        ).format(table), (message_id,))
        row = cursor.fetchone()
        if row is None:
            return {"status": "missing", "state": None}
        state, started = row
        if state == "cancelled":
            return {"status": "cancelled", "state": state}
        if state in ("done", "rejected"):
            return {"status": "terminal", "state": state}
        if started:
            cursor.execute(sql.SQL(
                "UPDATE {} SET cancel_requested = TRUE WHERE message_id = %s"
            ).format(table), (message_id,))
            return {"status": "requested", "state": state}
        cursor.execute(sql.SQL(
            "UPDATE {} SET state = 'cancelled', cancel_requested = TRUE, "
            "result = NULL, result_ttl = NULL WHERE message_id = %s"
        ).format(table), (message_id,))
        notify_cancelled(cursor, message_id, schema, prefix)
        return {"status": "cancelled", "state": "cancelled"}


def cancellation_status(pool, message_id, *, schema="dramatiq", prefix=""):
    with transaction(pool) as cursor:
        cursor.execute(sql.SQL(
            "SELECT state::text, cancel_requested FROM {} WHERE message_id = %s"
        ).format(sql.Identifier(schema, prefix + "queue")), (message_id,))
        row = cursor.fetchone()
        return {"state": row[0], "requested": row[1]} if row else {"state": None, "requested": False}
