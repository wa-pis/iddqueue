"""Dedicated PostgreSQL only: 100 messages, one warmup + five measured runs."""
import json
import statistics
import time
from uuid import uuid4

import psycopg
from dramatiq import Message
from psycopg import sql

from iddqueue import PostgresBroker, generate_init_sql
from iddqueue.utils import make_pool


class CountCursor(psycopg.Cursor):
    calls = statements = 0
    def execute(self, *args, **kw):
        if args[0]:  # Exclude empty connection-health commands.
            type(self).calls += 1
            type(self).statements += 1
        return super().execute(*args, **kw)
    def executemany(self, query, params_seq, **kw):
        params_seq = list(params_seq)
        type(self).calls += 1
        type(self).statements += len(params_seq)
        return super().executemany(query, params_seq, **kw)

def main():
    schema = 'batch_benchmark_' + uuid4().hex[:8]
    with psycopg.connect('', autocommit=True) as conn:
        conn.execute(generate_init_sql(schema))
    pool = make_pool('', maxconn=1)
    pool.kwargs['cursor_factory'] = CountCursor
    broker = PostgresBroker(pool=pool, schema=schema, results=False, middleware=[])
    try:
        output = {}
        for mode in ['single', 'batch']:
            timings = []
            counters = []
            for repetition in range(6):
                messages = [Message('benchmark', 'unused', (), {'value': i}, {}) for i in range(100)]
                CountCursor.calls = CountCursor.statements = 0
                start = time.perf_counter()
                if mode == 'single':
                    for message in messages:
                        broker.enqueue(message)
                else:
                    broker.enqueue_many(messages)
                elapsed = (time.perf_counter() - start) * 1000
                if repetition:
                    timings.append(elapsed)
                    counters.append((CountCursor.calls, CountCursor.statements))
            output[mode] = dict(median_ms=round(statistics.median(timings), 3),
                                samples_ms=[round(t, 3) for t in timings],
                                enqueue_calls_and_statements=counters, transactions=100 if mode == 'single' else 1)
        print(json.dumps(output))
    finally:
        broker.close()
        pool.close()
        with psycopg.connect('', autocommit=True) as conn:
            conn.execute(sql.SQL('DROP SCHEMA {} CASCADE').format(sql.Identifier(schema)))


if __name__ == "__main__":
    main()
