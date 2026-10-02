#
#       R E S U L T S
#
# Implements a result backend using Postgres. See
# https://dramatiq.io/cookbook.html#results.
#

import logging
import time
from textwrap import dedent

from dramatiq.results import ResultBackend, ResultMissing, ResultTimeout
from psycopg.types.json import Jsonb

from .utils import (
    QueryManager,
    make_pool,
    retry_pg,
    tidy4json,
    transaction,
    wait_for_notifies,
)

logger = logging.getLogger(__name__)


class PostgresBackend(ResultBackend):
    def __init__(self, *, url=None, pool=None, schema=None, prefix=None, **kw):
        super().__init__(**kw)

        if pool is not None and url:
            raise ValueError("You can't set both pool and URL!")
        self._owns_pool = pool is None
        self.pool = make_pool(url or "") if pool is None else pool

        self.queries = QueryManager(QUERIES.queries, schema or "dramatiq", prefix or "")

    def close(self):
        if self._owns_pool:
            self.pool.close()

    def build_message_key(self, message):
        # Just use message_id, it's UNIQUE in table.
        return str(message.message_id)

    @retry_pg
    def get_result(self, message, *, block=False, timeout=None):
        key = self.build_message_key(message)

        timeout = 300_000 if timeout is None else timeout
        deadline = time.monotonic() + timeout / 1000
        channel = f"dramatiq.{key}.results"
        with transaction(self.pool, listen=channel) as curs:
            while True:
                curs.execute(self.queries.GET, (key,))
                row = curs.fetchone()
                if row is not None:
                    return self.unwrap_result(row[0])
                if not block:
                    raise ResultMissing(message)
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    raise ResultTimeout(message)
                wait_for_notifies(curs.connection, timeout=remaining)

    @retry_pg
    def _store(self, key, result, ttl):
        with transaction(self.pool) as curs:
            logger.debug("Storing result for %s.", key)
            curs.execute(
                self.queries.STORE,
                (
                    key,
                    Jsonb(tidy4json(result)),
                    f"{ttl} ms",
                ),
            )
            if 0 == curs.rowcount:
                raise Exception(f"Can't store result of message {key}.")


QUERIES = QueryManager(
    dict(
        GET=dedent(
            """\
    SELECT result
        FROM {schema}.{tablename}
        WHERE message_id = %s AND result IS NOT NULL
          AND result_ttl > NOW();
    """
        ),
        STORE=dedent(
            """\
    WITH stored AS (
        INSERT INTO {schema}.{tablename}
                    (queue_name, message_id, "state", result, result_ttl)
            VALUES ('__RQ__', %s, 'done',
                    %s, NOW() + %s::interval)
        ON CONFLICT (message_id)
        DO UPDATE SET mtime = NOW(),
                        result = EXCLUDED.result,
                        result_ttl = EXCLUDED.result_ttl
        RETURNING queue_name, message_id, result
    )
    SELECT
        pg_notify('dramatiq.' || message_id || '.results', message_id::text)
    FROM stored;
    """
        ),
    )
)
