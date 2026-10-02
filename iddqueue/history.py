"""Optional per-execution diagnostics, independent of queue/result retention."""
from uuid import uuid4

from dramatiq.middleware import Middleware
from psycopg import sql

from .utils import transaction


def attempt_table(schema, prefix):
    return sql.Identifier(schema, prefix + "attempts")


class AttemptHistory(Middleware):
    def before_process_message(self, broker, message):
        attempt_id = uuid4()
        with transaction(broker.pool) as curs:
            curs.execute(sql.SQL(
                "INSERT INTO {} (attempt_id, message_id, queue_name, actor_name) VALUES (%s, %s, %s, %s)"
            ).format(attempt_table(broker.queries.schema, broker.queries.prefix)),
                         (attempt_id, message.message_id, message.queue_name, message.actor_name))
        message._pg_attempt_id = attempt_id

    def after_process_message(self, broker, message, *, result=None, exception=None):
        attempt_id = getattr(message, "_pg_attempt_id", None)
        if attempt_id is None:
            return
        with transaction(broker.pool) as curs:
            curs.execute(sql.SQL(
                "UPDATE {} SET finished_at = clock_timestamp(), outcome = %s, error_type = %s, "
                "error_text = %s WHERE attempt_id = %s"
            ).format(attempt_table(broker.queries.schema, broker.queries.prefix)),
                         ("successful" if exception is None else "failed",
                          type(exception).__name__ if exception is not None else None,
                          str(exception)[:2000] if exception is not None else None, attempt_id))


def list_attempts(pool, message_id, *, schema="dramatiq", prefix="", limit=50, after=None):
    if not 1 <= limit <= 1000:
        raise ValueError("limit must be between 1 and 1000")
    with transaction(pool) as curs:
        curs.execute(sql.SQL(
            "SELECT attempt_id, message_id, queue_name, actor_name, started_at, finished_at, "
            "COALESCE(outcome, 'incomplete'), error_type, error_text FROM {} "
            "WHERE message_id = %s AND (%s::uuid IS NULL OR attempt_id > %s) "
            "ORDER BY attempt_id LIMIT %s"
        ).format(attempt_table(schema, prefix)), (message_id, after, after, limit + 1))
        rows = curs.fetchall()
    names = ("attempt_id", "message_id", "queue", "actor", "started_at", "finished_at",
             "outcome", "error_type", "error_text")
    items = []
    for row in rows[:limit]:
        item = dict(zip(names, row))
        item["duration_ms"] = (row[5] - row[4]).total_seconds() * 1000 if row[5] else None
        for key in ("attempt_id", "message_id"):
            item[key] = str(item[key])
        for key in ("started_at", "finished_at"):
            item[key] = item[key].isoformat() if item[key] else None
        items.append(item)
    return dict(items=items, next_after=items[-1]["attempt_id"] if len(rows) > limit else None)


def purge_attempts(pool, maxage="30 days", *, schema="dramatiq", prefix=""):
    with transaction(pool) as curs:
        curs.execute("SELECT %s::interval > interval '0'", (maxage,))
        if not curs.fetchone()[0]:
            raise ValueError("maxage must be positive")
        curs.execute(sql.SQL("DELETE FROM {} WHERE started_at < clock_timestamp() - %s::interval")
                     .format(attempt_table(schema, prefix)), (maxage,))
        return curs.rowcount
