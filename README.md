# IDDQueue

[Dramatiq](https://dramatiq.io/) is a simple task queue implementation for
Python3. iddqueue provides a Postgres-based implementation of a dramatiq
broker.


## Features

- Super simple deployment: Single table, no ORM.
- Stores message payload and results as native JSONb.
- Uses LISTEN/NOTIFY to keep worker sync. No polling.
- Implements delayed task.
- Reliable thanks to Postgres MVCC.
- Self-healing: automatic purge of old messages. Automatic recovery after
  crash.
- Utility CLI for maintainance: flush, purge, stats, etc.

Note that dramatiq assumes tasks are idempotent. This broker makes the same
assumptions for recovering after a crash.


Renaming changes the distribution, Python imports and CLI to `iddqueue`.
Update application imports and deployment commands. Prometheus metrics now use
the `iddqueue_queue_` prefix; update dashboards. PostgreSQL tables, channels
and advisory lock identities remain unchanged.

## Installation

- Install the locally built wheel (PyPI publication is pending):
  ``` console
  $ pip install "dist/iddqueue-0.13.0-py3-none-any.whl[binary]"
  ```
  Requires Python 3.10+, Dramatiq 2.2.1+ and Psycopg 3.3.6+.
- Init database schema with `init` command.
  ``` console
  $ iddqueue init
  ```
  Or adapt `iddqueue/schema.sql` to your needs.
- Before importing actors, define global broker with a connection
  pool:
  ``` python
  import dramatiq
  from iddqueue import PostgresBroker

  dramatiq.set_broker(PostgresBroker(url="postgresql://localhost/postgres"))

  @dramatiq.actor
  def myactor():
      ...
  ```

Now declare/import actors and manage worker just like any [dramatiq
setup](https://dramatiq.io/guide.html). See the local [example](example.py)
and [documentation](docs/index.rst).

The CLI tool `iddqueue` manages queues and failed tasks. See `--help`.

## Integration

The upstream [django-dramatiq-pg](https://github.com/uptick/django-dramatiq-pg/)
integration by Curtis Maloney targets the original package. Compatibility with
IDDQueue has not been verified.

## Support

The new GitHub issue tracker will be linked after repository setup.
IDDQueue is available under the PostgreSQL licence.


## Credit

Thanks to all contributors :

- Andy Freeland
- Curtis Maloney, Django support.
- Federico Caselli, bugfixes.
- Giuseppe Papallo, bugfixes.
- Rafal Kwasny, improvements.


The upstream logo was created by [Damien CAZEILS](http://www.damiencazeils.com/).


## Development

```console
poetry install --extras "binary monitoring"
poetry run iddqueue init
poetry run python tests/pypsql < tests/func/schema.sql
poetry run pytest tests/unit tests/func
```

Configure the test database with `PGHOST`, `PGPORT`, `PGUSER`, `PGPASSWORD`
and `PGDATABASE`. Tests terminate database connections and restart workers;
use a dedicated test database. `docker-compose.yml` provides PostgreSQL 18.

Version 0.13 uses Psycopg 3 pools; Psycopg 2 pools are no longer supported.
Broker-created pools open on first use and default to zero idle connections.
Call `broker.close()` on shutdown. If you supply a pool, close it yourself
and create it separately in each worker process.


## Transactional publishing

Use `enqueue_in_transaction` to publish a task atomically with application
changes in the same PostgreSQL database:

```python
import psycopg

with psycopg.connect(dsn) as connection:
    with connection.transaction():
        connection.execute("UPDATE orders SET status = %s WHERE id = %s",
                           ("confirmed", order_id))
        broker.enqueue_in_transaction(send_receipt.message(order_id),
                                      connection=connection)
```

The connection must already have an active transaction. The broker does not
commit, roll back, close, or retry that transaction. PostgreSQL makes the task
and its notification visible on commit; rollback cancels both. `delay` is in
milliseconds, measured from enqueue time. Enqueue middleware hooks run around
the SQL operation: `after_enqueue` does not mean the outer transaction has
committed. Workers still provide at-least-once delivery.

### PostgreSQL limiters and group callbacks

Existing installations must add the coordination table before enabling this
backend. Fresh `iddqueue init` installations include it:

```python
import psycopg
from iddqueue import generate_coordination_sql

with psycopg.connect("postgresql://localhost/app") as connection:
    connection.execute(generate_coordination_sql(schema="dramatiq", prefix=""))
```

The upgrade is idempotent and preserves queue data. To reverse it, first stop
users of the coordination backend, then drop only `dramatiq.coordination`
(adjust schema and prefix when customized).

```python
from dramatiq.middleware import GroupCallbacks
from dramatiq.rate_limits import ConcurrentRateLimiter
from iddqueue import PostgresRateLimiterBackend

limits = PostgresRateLimiterBackend(pool=broker.pool)
broker.add_middleware(GroupCallbacks(limits, barrier_ttl=900_000))

with ConcurrentRateLimiter(limits, "external-api", limit=5).acquire():
    call_external_api()
```

The backend also supports `BucketRateLimiter`, `WindowRateLimiter` and `Barrier`.
Durations are milliseconds, except Dramatiq's sliding `window` in seconds.
Use unique UUID barrier keys. Events survive missed notifications until their
TTL expires. `wait` holds one pool connection; size the pool for simultaneous
waiters and publishers. Schedule `limits.purge()` periodically to remove
expired coordination rows. `close()` closes only a pool owned by the backend.

Choose a TTL longer than the longest operation: an expired concurrency slot
can be acquired while its original task is still running. Standard
`GroupCallbacks` counts successful deliveries; repeated deliveries can contribute
again and callbacks are not guaranteed exactly once. A group with failed tasks
may never reach its barrier, and expired group state cannot reconstruct progress.

### Standard Dramatiq composition and middleware

The broker supports the standard `dramatiq.pipeline` and `dramatiq.group` APIs.
Enable result storage on each actor whose result you want to retrieve:

```python
import dramatiq

@dramatiq.actor(store_results=True)
def multiply(value, factor=2):
    return value * factor

chain = dramatiq.pipeline([multiply.message(3), multiply.message(4)])
chain.run()
assert chain.get_result(block=True) == 24

batch = dramatiq.group([multiply.message(3), multiply.message(4)])
batch.run()
assert list(batch.get_results(block=True)) == [6, 8]
assert batch.completed_count == 2
```

Pipelines append a predecessor's result to the next actor's positional arguments.
A failed step does not enqueue its successor. `get_results` returns group results
in submission order; tasks may finish in another order. `completed_count` reads
stored results, so actors without result storage are not counted and expired
results no longer count. Terminal failures raise `ResultFailure`.

For coroutine actors, add Dramatiq's standard `AsyncIO` middleware before
declaring the actors, in the module loaded by every worker:

```python
import asyncio
from dramatiq.middleware import AsyncIO

broker.add_middleware(AsyncIO())

@dramatiq.actor(store_results=True)
async def async_task(value):
    await asyncio.sleep(0.01)
    return value
```

The PostgreSQL broker remains synchronous. Use async clients or
`asyncio.to_thread` for blocking I/O inside coroutine actors.

The default `Retries` middleware supports `on_retry_exhausted` (singular):

```python
@dramatiq.actor
def report_failure(message, retry_metadata):
    # message is a serialized Dramatiq message; metadata has
    # retries and max_retries. Make any external action idempotent.
    print(message["message_id"], retry_metadata)

@dramatiq.actor(max_retries=3, on_retry_exhausted="report_failure")
def unreliable_task():
    raise RuntimeError("unavailable")
```


`Actor.send_with_options(delay=timedelta(seconds=1))` accepts a `timedelta`;
Dramatiq converts it to milliseconds before calling the broker. Direct broker
methods use millisecond delays. A delay specifies the earliest execution time,
not an exact schedule.

Smaller actor `priority` numbers run first among messages already prefetched by
a worker. PostgreSQL does not provide global priority ordering across workers
or all queued messages. Ordinary groups need only Results; completion callbacks
additionally require `GroupCallbacks` and the PostgreSQL coordination table
shown above. Pipelines, retries and callbacks retain at-least-once delivery.

### Inspect and retry failed tasks

The broker records the last exception type, up to 2,000 characters of its text,
UTC timestamp and attempt number in `message.options.pg_failure`. The standard
Retries metadata remains available. Intermediate retries carry this metadata;
a successful attempt removes the last error. Existing rejected rows may have
no diagnostic metadata; no database migration is required.

```sh
iddqueue failed list --queue default --actor send_receipt --limit 50
iddqueue failed list --queue default --after MESSAGE_ID
iddqueue failed show MESSAGE_ID
iddqueue failed show MESSAGE_ID --payload
iddqueue retry MESSAGE_ID
```

These commands produce JSON. `failed list` returns `items` and `next_after`;
pass that cursor as `--after` with the same filters to continue. The default
page size is 50, with a maximum of 1,000. Pages use UUID order; concurrently
rejected tasks may require a fresh scan. `show` returns a nonzero exit code for
missing or non-rejected messages. Arguments, full options and traceback are
excluded unless `--payload` is explicitly requested. Exception text itself can
contain application values.

`retry` accepts only a rejected task whose worker has released its message lock.
It atomically preserves ID, actor and arguments, clears the old result and
retry-cycle fields (`retries`, `traceback`, `requeue_timestamp`, `eta`,
`pg_failure`), and publishes immediately to the normal queue. Other options,
including retry policy, remain unchanged. Refused retries return a nonzero exit
code; if the worker is still finishing rejection, retry after it releases the
lock. Concurrent retry requests allow only one transition to queued.

Use `--schemaname` and `--prefix` before the command for customized tables.
Diagnostic metadata is saved with queue state; tasks lost before acknowledgment
may not have it. Purge removes rejected tasks according to existing retention.
Only the latest error is retained. Retrying requires idempotent actors; it does
not reverse prior side effects or reset barriers and downstream pipelines.

### PostgreSQL queue metrics

`iddqueue stats` keeps its original state totals. Use `stats --json` for
per-queue snapshots, or `stats --queue default` for one queue (including zeros
when empty). Each snapshot includes all four stored-state counts, `ready`,
`scheduled` and `oldest_ready_seconds`.

Ready backlog includes only queued messages whose ETA has passed. Scheduled
messages include future ETAs in queued or consumed state, since Dramatiq can
prefetch delayed messages. Consumed means claimed/prefetched, not necessarily
executing. Delayed queue names remain separate (for example `default.DQ`).
Age starts at the later of the current enqueue time and ETA. Re-enqueue/recovery
resets enqueue time; original message timestamps do not measure the current
attempt. Existing queued rows use their existing `mtime`; no migration is needed.

Install `iddqueue[monitoring]` to enable Prometheus. For standard processing,
retry and duration metrics, add middleware in the worker's actor module:

```python
from dramatiq.middleware.prometheus import Prometheus

broker.add_middleware(Prometheus())
```

Its default endpoint is port 9191; Dramatiq supports `dramatiq_prom_host`,
`dramatiq_prom_port` and `dramatiq_prom_db`. The test example enables it only
when `EXAMPLE_PROMETHEUS=1` is set.

Register the PostgreSQL collector in a separate exporter process. Its pool
belongs to that process; keep it separate from worker multiprocessing state:

```python
from threading import Event
from prometheus_client import CollectorRegistry, start_http_server
from iddqueue.metrics import PostgresQueueCollector
from iddqueue.utils import make_pool

pool = make_pool("postgresql://localhost/app")
registry = CollectorRegistry()
registry.register(PostgresQueueCollector(pool))
start_http_server(9192, addr="127.0.0.1", registry=registry)
try:
    Event().wait()
finally:
    pool.close()
```

SQL metrics are `iddqueue_queue_messages` (queue/state),
`iddqueue_queue_ready`, `iddqueue_queue_scheduled` and
`iddqueue_queue_oldest_ready_seconds` (queue only). No message IDs or actor
arguments become labels. A collector may select one `queue`, `schema` or `prefix`.
Removed queues disappear from an unfiltered scrape; an explicitly selected
empty queue returns zero. Scrape errors propagate instead of returning false
zero backlog. The main broker does not import or require Prometheus.

Each scrape performs an aggregate over stored rows, including retained done
and rejected messages. Start with a 30–60 second scrape interval and measure on
your workload. A local PostgreSQL 14 test with 10,000 rows and 1 KB payloads took
about 2.85 ms for all queues and 1.08 ms for one queue using a sequential scan;
these are sample measurements, not production guarantees. Retention, payload
size and queue count affect cost; no additional index was justified by that test.

### Application storage isolation

Use a distinct `(schema, prefix)` pair for each application sharing one database:

```python
from iddqueue import PostgresBroker

first = PostgresBroker(schema="first_app", prefix="jobs_")
second = PostgresBroker(schema="second_app", prefix="jobs_")
```

Initialize each pair with `generate_init_sql(schema, prefix)` or the CLI's
`--schemaname` and `--prefix`. SQL, enqueue/ack/result notifications and message
locks use that same storage area. Identical queue names and UUIDs can be processed
independently in different areas, including large payloads fetched by ID.
Coordination backends and metrics collectors must use matching schema/prefix.
For shared pools, configure each backend explicitly with the same pair.

Results remain keyed by the message UUID. Dramatiq's logical `namespace` option
does not change SQL storage. `use_namespace_prefix_keys=True` raises `ValueError`;
use schema/prefix rather than a string key format for application isolation.
Different queue names alone do not isolate results with identical UUIDs.

The default area (`dramatiq`, empty prefix) retains existing short channel names
and message locks. Other areas use stable hashed channels bounded to 63 bytes;
long default queue names also use bounded channels. No schema migration is needed.

Before upgrading non-default areas (or long default queue names), stop producers,
drain or gracefully stop every worker using that area, and stop result waiters.
Upgrade all participants together, then restart workers, result readers and
producers with matching configurations. Do not mix old and new versions: their
channels and advisory locks differ. Persisted queued tasks and results remain in
the same tables; restarted workers recover queued tasks from those tables.
Rollback follows the same stop-and-restart sequence. This is application storage
separation, not PostgreSQL permissions; use database roles for access control.


### License and attribution

This project is a fork of [DALIBO's dramatiq-pg](https://gitlab.com/dalibo/dramatiq-pg),
originally credited to Étienne BERSAC and other upstream contributors.
The original `Copyright (c) 2019, DALIBO` and full [LICENSE](LICENSE) are preserved
in source, wheel and sdist. Package metadata identifies the PostgreSQL License.

The PostgreSQL License permits use, modification and distribution for any
purpose, including commercial use, provided the copyright notice and full
license text accompany distributed copies. See the
[official license text](https://www.postgresql.org/about/licence/).
Dependencies retain their own licenses. These permissions do not guarantee
that every possible legal claim is excluded. Publication and project naming
remain separate decisions.

After building, run `python scripts/check_license.py dist/*.whl dist/*.tar.gz`
to verify the preserved upstream text and license metadata in both formats.
