"""Queue snapshots; Prometheus is imported only when collecting metrics."""

from psycopg import sql

from .utils import transaction

STATES = ("queued", "consumed", "done", "rejected", "cancelled")


def statistics_query(schema="dramatiq", prefix=""):
    return sql.SQL("""
        SELECT queue_name,
            count(*) FILTER (WHERE state = 'queued'),
            count(*) FILTER (WHERE state = 'consumed'),
            count(*) FILTER (WHERE state = 'done'),
            count(*) FILTER (WHERE state = 'rejected'),
            count(*) FILTER (WHERE state = 'cancelled'),
            count(*) FILTER (WHERE state = 'queued' AND ready_at <= now()),
            count(*) FILTER (WHERE state IN ('queued', 'consumed') AND ready_at > now()),
            coalesce(greatest(0, extract(epoch FROM now() - min(ready_at)
                FILTER (WHERE state = 'queued' AND ready_at <= now()))), 0)
        FROM (
            SELECT *, greatest(mtime,
                to_timestamp(coalesce((message->'options'->>'eta')::double precision / 1000, 0))) AS ready_at
            FROM {} WHERE (%s::text IS NULL OR queue_name = %s)
        ) AS messages GROUP BY queue_name ORDER BY queue_name
    """).format(sql.Identifier(schema, prefix + "queue"))


def queue_statistics(pool, *, schema="dramatiq", prefix="", queue=None):
    with transaction(pool) as cursor:
        cursor.execute(statistics_query(schema, prefix), (queue, queue))
        rows = cursor.fetchall()
    snapshots = [dict(queue=row[0], counts=dict(zip(STATES, row[1:6])),
                      ready=row[6], scheduled=row[7], oldest_ready_seconds=float(row[8]))
                 for row in rows]
    if not snapshots and queue is not None:
        snapshots.append(dict(queue=queue, counts=dict.fromkeys(STATES, 0),
                              ready=0, scheduled=0, oldest_ready_seconds=0.0))
    return snapshots


class PostgresQueueCollector:
    """Register in an exporter process; the caller owns the pool."""

    def __init__(self, pool, *, schema="dramatiq", prefix="", queue=None):
        self.pool = pool
        self.options = dict(schema=schema, prefix=prefix, queue=queue)

    def describe(self):
        # Avoid database access during registry registration.
        return iter(())

    def collect(self):
        from prometheus_client.core import GaugeMetricFamily

        counts = GaugeMetricFamily("iddqueue_queue_messages", "Stored messages by state", labels=["queue", "state"])
        ready = GaugeMetricFamily("iddqueue_queue_ready", "Ready queued messages", labels=["queue"])
        scheduled = GaugeMetricFamily("iddqueue_queue_scheduled", "Future delayed messages, including prefetched", labels=["queue"])
        age = GaugeMetricFamily("iddqueue_queue_oldest_ready_seconds", "Age of oldest ready queued message", labels=["queue"])
        for snapshot in queue_statistics(self.pool, **self.options):
            queue = snapshot["queue"]
            for state, count in snapshot["counts"].items():
                counts.add_metric([queue, state], count)
            ready.add_metric([queue], snapshot["ready"])
            scheduled.add_metric([queue], snapshot["scheduled"])
            age.add_metric([queue], snapshot["oldest_ready_seconds"])
        yield from (counts, ready, scheduled, age)
