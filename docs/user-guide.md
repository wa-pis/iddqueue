# User Guide

## Connections and results

Construct `PostgresBroker(url=dsn)` or `PostgresBroker(pool=pool)` with a synchronous psycopg_pool.ConnectionPool; providing both is invalid. URL query parameters minconn/maxconn size the pool (defaults 0/16). A broker-created pool opens lazily and is closed by broker.close(); a supplied pool belongs to you. Create pools separately in each worker process.

Results middleware is enabled by default. Mark actors `store_results=True` and pass `backend=broker.backend` to get_result. `results=False` disables auto-registration. Standalone use: `PostgresBackend(url=dsn)` with `dramatiq.results.Results(backend=backend)`. Close owned backend pools too.

## Storage setup and isolation

`iddqueue init` creates the queue plus coordination, deduplication, queue_control, attempts and schedules tables. `iddqueue upgrade` idempotently adds optional storage, started/cancel_requested columns and cancelled state to existing installations without discarding queued messages or Results. Use schema/prefix consistently on brokers, backends, CLI and collectors. Results are UUID-keyed; Dramatiq's logical namespace does not isolate SQL. Stop all participants during migrations; see [deployment](deployment-guide.md).

## Publishing

Ordinary actor.send/send_with_options uses standard Dramatiq enqueue, retries and delayed queues. Transactional enqueue uses a caller-owned active Psycopg transaction in the same database as business writes. Commit makes tasks and notifications visible; rollback removes both. Hooks describe SQL execution, not the eventual external commit. The broker does not commit or retry your transaction. See [transactional examples](recipes.md#transactional-publishing).

Deduplication accepts a key and positive integer TTL in milliseconds. Keys are scoped to logical queue and storage area; concurrent duplicates return the original message. Use that returned message for Results. Expired keys allow new publication; purge of a queue row does not release a live key. Deduplication suppresses publication, not duplicate actor execution.

Batch enqueue accepts up to 1000 messages and an optional per-message options list (delay/deduplication_key/deduplication_ttl). It preserves input order and commits atomically. External batches use a savepoint in an active transaction; no batch API automatically retries an ambiguous disconnect. Detailed [batch and dedup examples](recipes.md) remain in README.

## Execution controls

Enable `PostgresBroker(queue_control=True)` on every participating worker to use pause and cancellation safely, including already prefetched messages. `iddqueue pause emails` and `resume emails` affect normal and delayed queues; publishing continues, paused tasks keep ETA/retry budget, and already authorized actors finish. The boundary is SQL start permission, not the first Python instruction.

`broker.cancel(message_id)` or `iddqueue cancel MESSAGE_ID` cancels before start; Results raises ResultCancelled. Running actors receive a cooperative request; they must check broker.cancellation_requested themselves. They are not interrupted. Cancelled UUIDs cannot be revived by retry/recover; send a new message for new work. Dedup may return the cancelled original until expiry.

## Coordination and Dramatiq middleware

PostgresRateLimiterBackend supports Dramatiq counters, window/bucket/concurrent limiters, barriers and group callbacks. Match broker schema/prefix; periodically purge expired coordination data. Pipelines/groups, async actors, callbacks, CurrentMessage, AgeLimit, TimeLimit and ShutdownNotifications use Dramatiq's standard implementations. TimeLimit is not a hard deadline for blocking system calls. Failure callbacks run on each failed attempt; use on_retry_exhausted for exhaustion. Callback side effects also require idempotency.

## Diagnostics and schedules

`iddqueue failed list/show` and `retry ID` inspect rejected tasks and start a fresh retry cycle; full payload is opt-in. Statistics include cancelled state. `attempt_history=True` adds diagnostic execution records; arguments/options/ results are omitted but exception text may contain application data. Incomplete records can mean running or crashed actors. Middleware failures can leave gaps: this is not an atomic audit log. Run history purge explicitly for retention.

PostgresScheduler persists fixed intervals, polls due rows and atomically publishes/advances each occurrence. Multiple schedulers share work using row locks. Missed intervals coalesce into one task; no cron/calendar or full replay. Pausing a destination still allows publication. Disable preserves queued tasks. Examples, CLI flags and detailed limitations: [recipes](recipes.md) and [API Reference](api.md).

## Async transaction input

0.13.0 includes explicit awaitable single/batch publication on a
caller-owned Psycopg AsyncConnection. The synchronous methods remain available. See the [async recipe](recipes.md#async-transactional-publishing)
for ownership, cancellation and synchronous hook limits. Workers and results remain synchronous.
