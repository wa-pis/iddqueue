# API Reference

IDDQueue ships a relatively simple API. Once you have initiated the broker, you're almost done with IDDQueue and can use Dramatiq as usual.

## `iddqueue.PostgresBroker(*, url="", pool=None, results=True, schema=None, prefix=None, queue_control=False, attempt_history=False)`

pool  

> A psycopg pool object. Should be ConnectionPool for thread safety.

url  

> A PostgreSQL connection string as understood by libpq. IDDQueue extends libpq URL-style connection string with `minconn` and `maxconn` parameters. Defaults to empty string, leading libpq to read values from environment variables.

results  

> a boolean indicating whether to initialize a result backend. Default is True.

A truthy url together with pool raises ValueError. Create an injected pool with autocommit enabled; the caller owns its lifecycle.

schema / prefix  

> Select PostgreSQL storage (defaults: dramatiq / empty prefix); initialize or upgrade that namespace before use. They also select notification/lock domains.

queue_control  

> Opt into pause/cancellation checks. Enable on every participating worker.

attempt_history  

> Opt into diagnostic execution records; requires the attempts table.

Both feature tables are included by current init/upgrade commands.

**Attributes**

backend  

> The PostgresBackend sharing the connection pool of the broker. Required to fetch result.

**Example**

Initialization:

``` python
from iddqueue import PostgresBroker

broker = PostgresBroker(url="postgresql://user:pass@host/dbname?maxconn=12")
import dramatiq
dramatiq.set_broker(broker)
```

Result usage:

``` python
message.get_result(backend=broker.backend)
```

## `iddqueue.PostgresBackend(*, url=None, pool=None, schema=None, prefix=None, **kwargs)`

Postgres-backed implementation of result storage for Dramatiq.

pool and url arguments have the same meaning and the same behaviour as for PostgresBroker.

## Transactional publishing

`broker.enqueue_in_transaction(message, *, connection, delay=None)` requires a synchronous Psycopg 3 connection with an active transaction. It returns the enqueued message, including the delayed queue and eta when `delay` is supplied in milliseconds. An idle connection raises `ValueError`; database errors propagate without automatic retries.

The caller owns commit, rollback and the connection. The task and its notification become visible only when the caller commits. A rollback removes both the task and the caller's business changes, provided they use the same PostgreSQL database. Enqueue middleware hooks describe the SQL operation, not the eventual commit of the external transaction.

## PostgreSQL coordination

`PostgresRateLimiterBackend(url=None, pool=None, schema="dramatiq", prefix="")` implements Dramatiq's standard rate-limiter and barrier backend. `add`, `incr`, `decr` and `incr_and_sum` use transaction-scoped advisory locks; `incr_and_sum` accepts a callable returning the current window's keys. TTL and wait timeouts are milliseconds. `wait(key, None)` waits without a deadline; events are durable until their TTL expires. Notifications carry no state and waiters always re-read the table.

`generate_coordination_sql(schema="dramatiq", prefix="")` returns an idempotent migration for existing installations. It does not alter the queue. `generate_init_sql` includes the same table for fresh installations. To reverse the migration, disable coordination users and drop only the schema's prefixed `coordination` table.

`purge()` deletes rows whose counter and event TTLs have both expired and returns the number removed. Run periodically for bucket/window workloads. The backend does not retry counter mutations after an ambiguous disconnect; callers must not assume a failed request was rolled back.

## Failure diagnostics

PostgresBroker installs FailureMetadata after its initial middleware so its `after_process_message` hook runs before the default Retries hook. The last exception is stored in `message.options.pg_failure` with `type`, `text` (maximum 2,000 characters), UTC `time` and one-based `attempt`. It is removed on success and persisted through the normal enqueue/ack/nack paths. No extra SQL writes or schema migration are needed. Diagnostic hook failures are logged by Dramatiq and do not replace the actor exception. Keep this hook after Retries in middleware registration order when customizing the middleware list.

The CLI `failed list/show` displays rejected messages as JSON; `retry ID` conditionally requeues a rejected row and clears its stale result. See the recipes for filters, cursor pagination, payload opt-in and retry-cycle semantics.

## Queue statistics

`queue_statistics(pool, *, schema="dramatiq", prefix="", queue=None)` from `iddqueue.metrics` returns a list of snapshots containing `queue`, `counts` for queued/consumed/done/rejected/cancelled, `ready`, `scheduled` and `oldest_ready_seconds`. It uses a single PostgreSQL statement and does not require Prometheus. Ready age uses the current enqueue timestamp and ETA; consumed rows are excluded from ready age. Empty selected queues return zeros.

`PostgresQueueCollector(pool, **options)` uses the same query and yields Prometheus gauges with queue/state labels. It imports prometheus_client only when collecting. Registry registration performs no database access. The caller owns the pool and should register the collector in a dedicated exporter process.

## Storage namespaces

Broker and Results isolate by `schema`/`prefix`. Notifications and message locks include that area for non-default configurations. Channels use a stable digest where needed and remain within PostgreSQL's 63-byte identifier limit. Default short channels and default message-lock keys retain their old format.

`PostgresBackend(use_namespace_prefix_keys=True)` raises `ValueError` with instructions to use schema/prefix; keys remain message UUIDs. `namespace` from the Dramatiq Results base class is logical metadata, not a SQL storage boundary. Custom coordination backends and collectors must match the broker's storage area. Upgrade all producers, workers and result waiters together after stopping the old processes. Namespace isolation itself does not rewrite stored UUIDs or tables. The complete upgrade from dramatiq-pg adds columns/enum values and feature tables; follow the [migration guide](migration.md).

## Extended broker API

`enqueue(message, *, delay=None, deduplication_key=None, deduplication_ttl=None)` and `enqueue_in_transaction(message, *, connection, ...)` return the published or original deduplicated Message. Delays and TTLs are milliseconds. `enqueue_many(messages, *, options=None)` and `enqueue_many_in_transaction(messages, *, connection, options=None)` return an ordered list, with a maximum of 1000 inputs. Options are one dict per input.

`pause_queue(queue)`, `resume_queue(queue)` and `queue_is_paused(queue)` control a logical queue. `cancel(message_id)` returns status/state; `cancellation_status(message_id)` returns state/requested and `cancellation_requested(message_id)` returns a boolean. Every worker must opt into queue_control for the SQL actor start gate.

`generate_init_sql(schema="dramatiq", prefix="")` initializes all storage; `generate_upgrade_sql(schema="dramatiq", prefix="")` adds optional storage idempotently without removing existing tasks. Both return SQL text for a synchronous Psycopg connection; apply with participants stopped.

`PostgresScheduler(broker)` from iddqueue.scheduler exposes `create(name, message, *, interval_ms, start_at=None)`, `list()`, `disable(name)` and `tick(*, limit=100)`. start_at must include a timezone. Creation returns a schedule UUID string; tick returns published Messages. Fixed intervals, coalescing and transactional boundaries are documented in [User Guide](user-guide.md) and [recipes](recipes.md).

CLI contracts and API stability: [SUPPORT](https://github.com/wa-pis/iddqueue/blob/main/SUPPORT.md).

## Domain actors (0.13.0rc3)

`Domain(name)` declares standard Dramatiq Actors with domain-derived queues.
Use `@domain.actor` or `@domain.actor(...)`, then `domain.register(broker)` at
startup. Actor names are qualified with the domain; options are validated on
registration. See [domain lifecycle and examples](domains.md). This additive API
is included since 0.13.0rc3.

Monitoring additions (0.13.0rc4): `domain_statistics(pool, *, domains=None, schema="dramatiq", prefix="")` and `PostgresDomainCollector(pool, **options)` from `iddqueue.metrics`. See [domain metric semantics](domains.md#domain-monitoring); these additions are included in RC4.

Optional adapter (0.13.0rc4): `iddqueue.sqlalchemy.enqueue_sqlalchemy(broker, message, *, connection, delay=None, deduplication_key=None, deduplication_ttl=None)`. See [SQLAlchemy transactions](sqlalchemy.md); included in RC4.
