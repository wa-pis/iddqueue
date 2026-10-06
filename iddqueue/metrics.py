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
                AND (%s::text[] IS NULL OR queue_name = ANY(%s::text[]))
        ) AS messages GROUP BY queue_name ORDER BY queue_name
    """).format(sql.Identifier(schema, prefix + "queue"))


def _queue_statistics(pool, *, schema="dramatiq", prefix="", queue=None, queues=None):
    with transaction(pool) as cursor:
        cursor.execute(statistics_query(schema, prefix), (queue, queue, queues, queues))
        rows = cursor.fetchall()
    snapshots = [dict(queue=row[0], counts=dict(zip(STATES, row[1:6])),
                      ready=row[6], scheduled=row[7], oldest_ready_seconds=float(row[8]))
                 for row in rows]
    if not snapshots and queue is not None:
        snapshots.append(dict(queue=queue, counts=dict.fromkeys(STATES, 0),
                              ready=0, scheduled=0, oldest_ready_seconds=0.0))
    return snapshots


def queue_statistics(pool, *, schema="dramatiq", prefix="", queue=None):
    return _queue_statistics(pool, schema=schema, prefix=prefix, queue=queue)


def domain_statistics(pool, *, domains=None, schema="dramatiq", prefix=""):
    if domains is not None:
        if isinstance(domains, str):
            raise TypeError("domains must be an iterable of domain names, not a string")
        domains = sorted(set(domains))
        if any(not isinstance(name, str) or not name or name.endswith(".DQ") for name in domains):
            raise ValueError("domains must contain nonempty names without the reserved .DQ suffix")
    queues = None if domains is None else [queue for name in domains for queue in (name, name + ".DQ")]
    snapshots = {}
    for row in _queue_statistics(pool, schema=schema, prefix=prefix, queues=queues):
        domain = row["queue"][:-3] if row["queue"].endswith(".DQ") else row["queue"]
        result = snapshots.setdefault(domain, dict(domain=domain, counts=dict.fromkeys(STATES, 0),
                                                   ready=0, scheduled=0, oldest_ready_seconds=0.0))
        for state in STATES:
            result["counts"][state] += row["counts"][state]
        result["ready"] += row["ready"]
        result["scheduled"] += row["scheduled"]
        result["oldest_ready_seconds"] = max(result["oldest_ready_seconds"], row["oldest_ready_seconds"])
    for domain in domains or ():
        snapshots.setdefault(domain, dict(domain=domain, counts=dict.fromkeys(STATES, 0),
                                          ready=0, scheduled=0, oldest_ready_seconds=0.0))
    return [snapshots[name] for name in sorted(snapshots)]


class PostgresQueueCollector:
    """Register in an exporter process; the caller owns the pool."""

    metric_prefix = "iddqueue_queue"
    label = "queue"
    snapshot = staticmethod(queue_statistics)

    def __init__(self, pool, *, schema="dramatiq", prefix="", queue=None):
        self.pool = pool
        self.options = dict(schema=schema, prefix=prefix, queue=queue)

    def describe(self):
        # Avoid database access during registry registration.
        return iter(())

    def collect(self):
        from prometheus_client.core import GaugeMetricFamily

        counts = GaugeMetricFamily(f"{self.metric_prefix}_messages", "Stored messages by state", labels=[self.label, "state"])
        ready = GaugeMetricFamily(f"{self.metric_prefix}_ready", "Ready queued messages", labels=[self.label])
        scheduled = GaugeMetricFamily(f"{self.metric_prefix}_scheduled", "Future delayed messages, including prefetched", labels=[self.label])
        age = GaugeMetricFamily(f"{self.metric_prefix}_oldest_ready_seconds", "Age of oldest ready queued message", labels=[self.label])
        for snapshot in self.snapshot(self.pool, **self.options):
            queue = snapshot[self.label]
            for state, count in snapshot["counts"].items():
                counts.add_metric([queue, state], count)
            ready.add_metric([queue], snapshot["ready"])
            scheduled.add_metric([queue], snapshot["scheduled"])
            age.add_metric([queue], snapshot["oldest_ready_seconds"])
        yield from (counts, ready, scheduled, age)


class PostgresDomainCollector(PostgresQueueCollector):
    """Domain gauges; caller owns the pool, actor imports are not required."""

    metric_prefix = "iddqueue_domain"
    label = "domain"
    snapshot = staticmethod(domain_statistics)

    def __init__(self, pool, *, schema="dramatiq", prefix="", domains=None):
        self.pool = pool
        self.options = dict(schema=schema, prefix=prefix, domains=None if domains is None else tuple(domains))
        if isinstance(domains, str):
            raise TypeError("domains must be an iterable of domain names, not a string")
