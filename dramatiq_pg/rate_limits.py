"""PostgreSQL storage for Dramatiq's standard limiters and barriers."""

import hashlib
import time

from dramatiq.rate_limits.backend import RateLimiterBackend
from psycopg import sql

from .utils import make_pool, transaction, wait_for_notifies


class PostgresRateLimiterBackend(RateLimiterBackend):
    def __init__(self, *, url=None, pool=None, schema="dramatiq", prefix=""):
        if pool is not None and url:
            raise ValueError("You can't set both pool and URL!")
        self._owns_pool = pool is None
        self.pool = make_pool(url or "") if pool is None else pool
        self.table = sql.Identifier(schema, prefix + "coordination")
        self.namespace = schema + "\0" + prefix + "\0"

    def close(self):
        if self._owns_pool:
            self.pool.close()

    def _digest(self, key):
        return hashlib.sha256((self.namespace + key).encode()).digest()

    def _lock(self, curs, keys):
        # Every counter mutation uses the same locks, including missing rows.
        locks = {int.from_bytes(self._digest(key)[:8], "big", signed=True) for key in keys}
        for lock in sorted(locks):
            curs.execute("SELECT pg_advisory_xact_lock(%s)", (lock,))

    def _values(self, curs, keys):
        curs.execute(sql.SQL(
            "SELECT key, value FROM {} WHERE key = ANY(%s) "
            "AND expires_at > clock_timestamp()"
        ).format(self.table), (list(keys),))
        return dict(curs.fetchall())

    def _put(self, curs, key, value, ttl):
        curs.execute(sql.SQL(
            "INSERT INTO {} AS target (key, value, expires_at) "
            "VALUES (%s, %s, clock_timestamp() + %s * interval '1 millisecond') "
            "ON CONFLICT (key) DO UPDATE SET value = EXCLUDED.value, "
            "expires_at = EXCLUDED.expires_at"
        ).format(self.table), (key, value, ttl))

    def add(self, key, value, ttl):
        with transaction(self.pool) as curs:
            self._lock(curs, [key])
            if key in self._values(curs, [key]):
                return False
            self._put(curs, key, value, ttl)
            return True

    def _change(self, key, amount, bound, ttl, *, decrement=False):
        with transaction(self.pool) as curs:
            self._lock(curs, [key])
            value = self._values(curs, [key]).get(key, 0) + amount
            if (value < bound) if decrement else (value > bound):
                return False
            self._put(curs, key, value, ttl)
            return True

    def incr(self, key, amount, maximum, ttl):
        return self._change(key, amount, maximum, ttl)

    def decr(self, key, amount, minimum, ttl):
        return self._change(key, -amount, minimum, ttl, decrement=True)

    def incr_and_sum(self, key, keys, amount, maximum, ttl):
        while True:
            with transaction(self.pool) as curs:
                window_keys = list(keys())
                self._lock(curs, [key, *window_keys])
                # The window may advance while this transaction waits for locks.
                # Restart to lock its new keys in the same global order.
                if list(keys()) != window_keys:
                    continue
                values = self._values(curs, [key, *window_keys])
                value = values.get(key, 0) + amount
                if value > maximum or amount + sum(values.get(k, 0) for k in window_keys) > maximum:
                    return False
                self._put(curs, key, value, ttl)
                return True

    def _channel(self, key):
        return "dpg.c." + self._digest(key).hex()[:48]

    def wait(self, key, timeout):
        deadline = None if timeout is None else time.monotonic() + timeout / 1000
        with transaction(self.pool, listen=self._channel(key)) as curs:
            while True:
                curs.execute(sql.SQL(
                    "SELECT 1 FROM {} WHERE key = %s "
                    "AND event_expires_at > clock_timestamp()"
                ).format(self.table), (key,))
                if curs.fetchone() is not None:
                    return True
                remaining = None if deadline is None else deadline - time.monotonic()
                if remaining is not None and remaining <= 0:
                    return False
                wait_for_notifies(curs.connection, timeout=remaining)

    def wait_notify(self, key, ttl):
        with transaction(self.pool) as curs:
            curs.execute(sql.SQL(
                "INSERT INTO {} (key, event_expires_at) "
                "VALUES (%s, clock_timestamp() + %s * interval '1 millisecond') "
                "ON CONFLICT (key) DO UPDATE SET event_expires_at = EXCLUDED.event_expires_at"
            ).format(self.table), (key, ttl))
            curs.execute("SELECT pg_notify(%s, '')", (self._channel(key),))

    def purge(self):
        """Remove expired counters and events; schedule periodically."""
        with transaction(self.pool) as curs:
            curs.execute(sql.SQL(
                "DELETE FROM {} WHERE expires_at <= clock_timestamp() "
                "AND event_expires_at <= clock_timestamp()"
            ).format(self.table))
            return curs.rowcount
