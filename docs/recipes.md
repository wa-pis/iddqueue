# IDDQueue recipes

Detailed examples for the PostgreSQL broker. Start with the [README](https://github.com/wa-pis/iddqueue/blob/main/README.md),
[user guide](user-guide.md) and [API reference](api.md).

Build your own example with the [recipe authoring guide](custom-recipes.md).

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

### Async transactional publishing

Available in **0.13.0rc5**.
Use the same active Psycopg AsyncConnection for your business SQL and publication:

```python
async with connection.transaction():
    await connection.execute("UPDATE orders SET status = %s WHERE id = %s",
                             ("confirmed", order_id))
    message = await broker.enqueue_in_transaction_async(
        send_receipt.message(order_id), connection=connection,
        deduplication_key=str(order_id), deduplication_ttl=60000,
    )
```

For a batch, use `await broker.enqueue_many_in_transaction_async(messages,
connection=connection, options=options)`, where options is one dictionary per
message (delay/deduplication_key/deduplication_ttl); the limit is 1000 messages.
Results preserve input order. Duplicate keys return the existing Message.
Batch and deduplication operations use an internal savepoint: failure rolls back
their writes, not earlier business writes. The caller decides whether to commit
the surrounding transaction.

The connection must already be in an active transaction in the same database
with the broker's schema/prefix. There is no implicit BEGIN, pool fallback,
commit, close or retry. Exceptions and cancellation propagate; after a failed
single SQL statement the caller must roll back before reusing that transaction.
Let your outer transaction context handle cancellation. A cancellation after
publication does not undo a transaction already committed; delivery remains
at least once and a lost commit response has an uncertain outcome.

Enqueue hooks remain synchronous on the event loop and describe SQL execution,
not external commit. Keep custom hooks short; blocking hooks still block the
loop. This API does not change actor.send, result retrieval or worker I/O.
The SQLAlchemy adapter still accepts synchronous Connection/Session only.

The [runnable isolated example](async-transaction.py) creates and removes its own
schema and verifies an actor result. Run against a dedicated local PostgreSQL
with PGHOST/PGPORT/PGUSER/PGDATABASE configured, from a checkout matching the installed RC5:

```bash
IDDQUEUE_TEST_DATABASE=dedicated uv run --locked --extra binary python docs/async-transaction.py
```

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
when empty). Each snapshot includes all five stored-state counts, `ready`,
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
long default queue names also use bounded channels. Namespace isolation alone
requires no DDL; upgrading from dramatiq-pg still requires the migration guide.

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
The original `Copyright (c) 2019, DALIBO` and full [LICENSE](https://github.com/wa-pis/iddqueue/blob/main/LICENSE) are preserved
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

### Deduplicated publishing

Upgrade existing storage with `iddqueue upgrade` (or
`generate_upgrade_sql(schema, prefix)`) before using deduplication.
Fresh `init` includes the table. Stop workers during schema upgrades.

Call the broker explicitly; these keywords are broker API parameters, not
Dramatiq actor options:

```python
message = broker.enqueue(
    send_receipt.message(order_id),
    deduplication_key=f"receipt:{order_id}",
    deduplication_ttl=60_000,
)
```

The TTL is a positive integer in milliseconds measured by PostgreSQL from the
key claim. The key belongs to the logical queue (normal and delayed share it)
within the configured schema/prefix. Concurrent calls return the original
message, including its ID, arguments and delay; a duplicate does not overwrite
the task, emit another notification or run enqueue hooks again. Use the returned
message when requesting Results. After TTL expires, the key can publish again.

The same parameters work with `enqueue_in_transaction(..., connection=conn)`.
A savepoint makes the key and task atomic when the caller catches an error.
Outer rollback removes both; notifications become visible only after commit.
As with ordinary transactional enqueue, hooks describe the SQL operation, not
the final outer commit. Retry middleware continues to use ordinary enqueue.

Queue purge does not release a live key: duplicates still return the original
message even if its row/result has been removed. Deduplication retains the
original message payload until the key is replaced or its expired row is
removed. It prevents duplicate publication; workers retain at-least-once
delivery, and actor side effects must remain idempotent. For workloads with
many unique keys, remove expired deduplication rows periodically with SQL;
only delete rows whose `expires_at <= clock_timestamp()`.


### Pause and resume queues

Run `iddqueue upgrade` on existing storage first. Enable queue control in every
worker broker for that storage area:

```python
broker = PostgresBroker(queue_control=True)
broker.pause_queue("emails")
broker.resume_queue("emails")
assert not broker.queue_is_paused("emails")
```

```sh
iddqueue pause emails
iddqueue queue-status emails
iddqueue resume emails
```

CLI commands return JSON; schema/prefix flags precede the command.
Control is opt-in to preserve operation against databases without the new table.
Every participating worker must enable it; a worker without queue control
ignores pause. Stop all participants for the upgrade and restart them with
matching configuration. The example enables it with `EXAMPLE_QUEUE_CONTROL=1`.

Pause persists across worker restarts. Publishing continues; both the normal
and delayed queue stop starting actors, and prefetched tasks return to queued.
Their ETA and retry budget remain intact; pause does not produce a Results
value or trigger terminal skip callbacks. Already authorized actors finish
normally. The start boundary is the commit of the SQL permission gate directly
before actor hooks; pause serializes with this gate, not the Python function's
first instruction. Gate database failures defer execution instead of allowing it.

Resume is idempotent and notifies both queue listeners to scan durable rows.
It also handles a resume racing with acknowledgment of a deferred message.
Pausing one logical queue affects neither other queues nor other schema/prefix
areas. Queue control middleware must remain first in the middleware list;
place additional middleware after it.


### Cancel tasks

Run `iddqueue upgrade` with workers stopped before upgrading this version:
the queue gains `started`/`cancel_requested` columns and a `cancelled` enum
value. Restart all participants together; enable `queue_control=True` on every
worker to protect prefetched tasks and serialize cancellation with actor start.

```python
outcome = broker.cancel(message.message_id)
status = broker.cancellation_status(message.message_id)
```

```sh
iddqueue cancel MESSAGE_ID
iddqueue cancel-status MESSAGE_ID
```

Cancel returns JSON-compatible `status` and `state`: `cancelled` for a task
cancelled before its start permission, `requested` for an already started task,
`terminal` for done/rejected, or `missing` (CLI exits nonzero).
Repeated cancellation is idempotent. Cancel-status includes `state` and
`requested`. Existing completed Results remain intact.

Queued, delayed and prefetched cancellations never call the actor. Results
raises `iddqueue.ResultCancelled` (a `ResultFailure` subclass), including for
a waiter already blocked when cancellation commits. No retry/ack/nack/recover
operation may revive a cancelled row. Queue statistics expose the additional
`cancelled` state; purge uses the same retention policy as done/rejected.
After the cancellation row is purged, Results follows ordinary missing semantics.

Running actors are not interrupted. They may check the request between chunks,
using standard `CurrentMessage` middleware:

```python
from dramatiq.middleware import CurrentMessage

broker.add_middleware(CurrentMessage())

@dramatiq.actor(store_results=True)
def work():
    message = CurrentMessage.get_current_message()
    for chunk in chunks():
        if broker.cancellation_requested(message.message_id):
            return {"stopped": True}
        process(chunk)
```

An actor that returns after cooperative cleanup completes normally with its
returned result. If a requested task retries, the next start gate cancels that
attempt. Do not reset cancellation by reusing its UUID; publish a new message
for a fresh execution. Deduplication may return a cancelled original until its
key TTL expires. At-least-once side effects still require idempotency.

### Standard middleware compatibility

IDDQueue uses Dramatiq's standard middleware implementations. AgeLimit,
TimeLimit, ShutdownNotifications and Callbacks are included in Dramatiq's
default middleware list; CurrentMessage is opt-in.

- Set actor/message `max_age` in milliseconds to reject expired messages.
  Age is measured from the original message timestamp, including retries.
  The actor is skipped, the row becomes rejected, its lock is released, and
  stored Results report the skip as a failure.
- Set `time_limit` in milliseconds to interrupt a CPU-bound actor on supported
  CPython. The exception follows the ordinary retry budget and Results path.
  This is not a hard wall-clock deadline: interrupts wait for Python/GIL
  execution and cannot cancel blocking system calls.
- Set `notify_shutdown=True` to receive `Shutdown` during worker shutdown.
  Catch it for cleanup. Returning completes normally; raising it follows
  ordinary failure/retry handling. Cleanup must remain idempotent.
- `on_success` sends `(original_message_dict, result)` to a callback actor.
  `on_failure` sends `(original_message_dict, {"type": ..., "message": ...})`
  on **each failed attempt**, including attempts that will retry.
  Use `on_retry_exhausted` for a callback specifically on exhausted retries.
  Callback side effects are subject to at-least-once delivery.
- Add `CurrentMessage()` to access the current message ID/options from an
  actor. Its context is cleared after processing, including actor failures;
  calls outside actor processing return `None`.

The integration suite checks actual PostgreSQL queue states, Results and
released advisory locks. Shutdown coverage runs the normal Dramatiq CLI in
separate processes and sends SIGTERM; it verifies actor cleanup and completion.

### Attempt history

Run `iddqueue upgrade` in each schema/prefix before enabling
`PostgresBroker(attempt_history=True)`. History is disabled by default.
Each actor execution gets a separate UUID, including retries of the same
message. Records contain actor/queue names, PostgreSQL start/finish times,
`successful` or `failed`, duration, and error type/text (at most 2000 characters).
Arguments, options and results are never stored in history. Exception text can
still contain application data.

```sh
iddqueue history list MESSAGE_UUID --limit 50
iddqueue history list MESSAGE_UUID --limit 50 --after ATTEMPT_UUID
iddqueue history purge --maxage '30 days'
# Global --schemaname / --prefix select the storage namespace.
```

Listing uses UUID cursor order, not chronological order; timestamps identify
execution order. `next_after` is null on the last page. An attempt without a
finish record is reported as `incomplete`: it may still be running, or the worker
may have died. A later execution creates a new record and preserves that entry.
Skips before actor execution (including pause/cancel/age expiry) create no record.
History is diagnostic middleware, not an atomic audit of actor side effects:
Dramatiq logs middleware database failures, and an unavailable database can leave
gaps or incomplete entries.

Retention is explicit: schedule `history purge` yourself with a positive
PostgreSQL interval. It deletes attempts by start time, including old incomplete
entries, independently of queued messages and Results. There is no automatic
cleanup thread. Enabling history adds two database transactions per execution.

### Atomic batch publishing

```python
messages = [first_actor.message(), second_actor.message()]
options = [{}, {"delay": 1000, "deduplication_key": "second", "deduplication_ttl": 60000}]
returned = broker.enqueue_many(messages, options=options)

with connection.transaction():
    # Business writes and the whole batch commit or roll back together.
    returned = broker.enqueue_many_in_transaction(
        messages, connection=connection, options=options)
```

The returned list follows input order; a deduplicated entry returns the original
message. `options` is optional, with one dict per message; dict keys are the same
`delay`, `deduplication_key`, `deduplication_ttl` keywords as `enqueue`. A batch is
limited to 1000 messages; an empty batch performs no SQL. The external form
requires an active transaction even for an empty batch and uses a savepoint,
so a caught batch error leaves earlier caller writes intact. Neither batch API
automatically retries a connection failure; the caller must handle an uncertain
commit with idempotency/deduplication.

Without deduplication, Psycopg `executemany` pipelines the existing per-message
SQL in one transaction. Deduplicated/mixed batches reuse the normal key claim
path in one transaction. All database writes and notifications roll back on any
error; notifications become visible only after the outer commit. Enqueue hooks
run once per published message; duplicates run none. Before hooks precede the
writes, after hooks run after successful writes (and after commit for the owned
transaction). External hooks describe the SQL operation and may run before the
caller subsequently rolls back. Python hook side effects cannot be rolled back.

### PostgreSQL interval scheduler

Upgrade each namespace before use: `iddqueue upgrade`. Schedules persist a
Dramatiq message template and a positive fixed interval in milliseconds. Workers
must register the actor; the scheduler does not import or execute actor code.

```sh
iddqueue schedule create reports generate_report --queue reports --interval-ms 60000 \
  --kwargs '{"account": 42}'
iddqueue schedule list
iddqueue scheduler --poll-ms 1000
iddqueue scheduler --once
iddqueue schedule disable reports
```

`--args` accepts a JSON array; `--kwargs` and `--options` accept JSON objects.
`--start-at` accepts an ISO timestamp with a timezone. By default the first run
is immediately due according to PostgreSQL. Times are stored as timestamptz and
listed in UTC. Names are unique within `--schemaname`/`--prefix`; create does not
overwrite a schedule. The Python API is `PostgresScheduler(broker)` from
`iddqueue.scheduler`, with `create(name, message, interval_ms=..., start_at=...)`,
`list()`, `disable(name)` and `tick(limit=100)`.

Multiple foreground scheduler processes can share the namespace: row locks with
`SKIP LOCKED` select due schedules. Publishing and advancing `next_run` commit in
one transaction. A crash before commit leaves the occurrence due; a crash after
commit leaves its message queued and its next run advanced. Each occurrence uses
a deterministic message UUID and the reserved dedup key prefix
`iddqueue:schedule:` (seven-day TTL). Expiry allows key reuse; it does not delete dedup rows. Delivery by workers is still at least once.

Missed intervals coalesce into one task, then advance to the next future point
on the original interval grid using PostgreSQL time. There is no cron/calendar
syntax or replay of every missed run. A paused destination still receives queued
occurrences; resume lets workers process them. Disable waits for an in-flight
scheduler transaction and prevents future publications while preserving queued
tasks. SIGTERM/SIGINT lets the current tick finish, then exits and closes the CLI
pool. Database errors exit the foreground process; a service manager may restart
it. Polling and actor enqueue hooks may add latency to short intervals.


### Consumer notification consistency

NOTIFY is a wakeup hint, including legacy full-message payloads. Workers claim
only their own queue and read the authoritative actor payload atomically from
PostgreSQL. Stale notifications for deleted, terminal, or moved messages are
skipped. ACK/NACK session locks are drained before the next consumer claim or
prefetch wait, even with a continuous backlog; retries retain their unlock
wakeup. This preserves at-least-once delivery, not exactly-once side effects.
