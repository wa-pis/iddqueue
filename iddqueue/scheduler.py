"""Fixed intervals; PostgreSQL owns time and the occurrence commit boundary."""
from datetime import timezone
from uuid import uuid4, uuid5

from dramatiq import Message
from psycopg import sql
from psycopg.types.json import Jsonb

from .utils import tidy4json, transaction


class PostgresScheduler:
    def __init__(self, broker):
        self.broker = broker
        self.table = sql.Identifier(broker.queries.schema, broker.queries.prefix + "schedules")

    def create(self, name, message, *, interval_ms, start_at=None):
        if not isinstance(name, str) or not name:
            raise ValueError("schedule name must be nonempty")
        if type(interval_ms) is not int or not 0 < interval_ms <= 2**63 - 1:
            raise ValueError("interval_ms must be positive bigint milliseconds")
        if start_at is not None and (start_at.tzinfo is None or start_at.utcoffset() is None):
            raise ValueError("start_at must include a timezone")
        schedule_id = uuid4()
        with transaction(self.broker.pool) as curs:
            curs.execute(sql.SQL(
                "INSERT INTO {} (schedule_id, name, message, interval_ms, next_run) "
                "VALUES (%s, %s, %s, %s, COALESCE(%s::timestamptz, clock_timestamp()))"
            ).format(self.table), (schedule_id, name, Jsonb(tidy4json(message)), interval_ms, start_at))
        return str(schedule_id)

    def list(self):
        with transaction(self.broker.pool) as curs:
            curs.execute(sql.SQL(
                "SELECT schedule_id, name, message->>'actor_name', message->>'queue_name', "
                "interval_ms, next_run, enabled FROM {} ORDER BY name"
            ).format(self.table))
            rows = curs.fetchall()
        return [dict(schedule_id=str(i), name=n, actor=a, queue=q, interval_ms=interval,
                     next_run=due.astimezone(timezone.utc).isoformat(), enabled=enabled)
                for i, n, a, q, interval, due, enabled in rows]

    def disable(self, name):
        with transaction(self.broker.pool) as curs:
            curs.execute(sql.SQL("UPDATE {} SET enabled = FALSE WHERE name = %s").format(self.table), (name,))
            return bool(curs.rowcount)

    def tick(self, *, limit=100):
        """Publish due rows once, coalescing missed intervals; no automatic retry."""
        if type(limit) is not int or not 1 <= limit <= 1000:
            raise ValueError("limit must be between 1 and 1000")
        published = []
        with transaction(self.broker.pool) as curs:
            curs.execute("SELECT clock_timestamp()")
            now = curs.fetchone()[0]
            curs.execute(sql.SQL(
                "SELECT schedule_id, message, next_run FROM {} WHERE enabled AND next_run <= %s "
                "ORDER BY next_run, schedule_id LIMIT %s FOR UPDATE SKIP LOCKED"
            ).format(self.table), (now, limit))
            for schedule_id, payload, due in curs.fetchall():
                occurrence = due.astimezone(timezone.utc).isoformat()
                message = Message(**payload).copy(
                    message_id=str(uuid5(schedule_id, occurrence)), message_timestamp=int(now.timestamp() * 1000))
                message = self.broker.enqueue_in_transaction(
                    message, connection=curs.connection,
                    deduplication_key=f"iddqueue:schedule:{schedule_id}:{occurrence}",
                    deduplication_ttl=7 * 24 * 60 * 60 * 1000)
                curs.execute(sql.SQL(
                    "WITH tick AS (SELECT clock_timestamp() AS now) UPDATE {} "
                    "SET next_run = next_run + (floor(extract(epoch FROM (tick.now - next_run)) "
                    "* 1000 / interval_ms) + 1) * interval_ms * interval '1 millisecond' "
                    "FROM tick WHERE schedule_id = %s"
                ).format(self.table), (schedule_id,))
                published.append(message)
        return published
