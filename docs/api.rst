===============
 API Reference
===============

Dramatiq-pg ships a relatively simple API. Once you have initiated the broker,
you're almost done with Dramatiq-pg and can use Dramatiq as usual.


``dramatiq_pg.PostgresBroker(url="", pool=None, results=True)``
===============================================================

:pool:

   A psycopg pool object. Should be ConnectionPool for thread safety.

:url:

   A PostgreSQL connection string as understood by libpq. Dramatiq-pg extends
   libpq URL-style connection string with ``minconn`` and ``maxconn``
   parameters. Defaults to empty string, leading libpq to read values from
   environment variables.

:results:

   a boolean indicating whether to initialize a result backend. Default is True.

Defining both pool and url raises a ValueError.

**Attributes**

:backend:

   The PostgresBackend sharing the connection pool of the broker. Required to
   fetch result.


**Example**

Initialization:

.. code:: python

   from dramatiq_pg import PostgresBroker

   broker = PostgresBroker("postgresql://user:pass@host/dbname?maxconn=12")
   set_broker(broker)


Result usage:

.. code:: python

   message.get_result(backend=broker.backend)


``dramatiq_pg.PostgresBackend(url="", pool=None)``
==================================================

Postgres-backed implementation of result storage for Dramatiq.

pool and url arguments have the same meaning and the same behaviour as for
PostgresBroker.


Transactional publishing
========================

``broker.enqueue_in_transaction(message, *, connection, delay=None)``
requires a synchronous Psycopg 3 connection with an active transaction.
It returns the enqueued message, including the delayed queue and eta when
``delay`` is supplied in milliseconds. An idle connection raises
``ValueError``; database errors propagate without automatic retries.

The caller owns commit, rollback and the connection. The task and its
notification become visible only when the caller commits. A rollback removes
both the task and the caller's business changes, provided they use the same
PostgreSQL database. Enqueue middleware hooks describe the SQL operation,
not the eventual commit of the external transaction.

PostgreSQL coordination
=======================

``PostgresRateLimiterBackend(url=None, pool=None, schema="dramatiq", prefix="")``
implements Dramatiq's standard rate-limiter and barrier backend. ``add``,
``incr``, ``decr`` and ``incr_and_sum`` use transaction-scoped advisory locks;
``incr_and_sum`` accepts a callable returning the current window's keys.
TTL and wait timeouts are milliseconds. ``wait(key, None)`` waits without a
deadline; events are durable until their TTL expires. Notifications carry no
state and waiters always re-read the table.

``generate_coordination_sql(schema="dramatiq", prefix="")`` returns an
idempotent migration for existing installations. It does not alter the queue.
``generate_init_sql`` includes the same table for fresh installations.
To reverse the migration, disable coordination users and drop only the
schema's prefixed ``coordination`` table.

``purge()`` deletes rows whose counter and event TTLs have both expired and
returns the number removed. Run periodically for bucket/window workloads.
The backend does not retry counter mutations after an ambiguous disconnect;
callers must not assume a failed request was rolled back.

Failure diagnostics
===================

PostgresBroker installs FailureMetadata after its initial middleware so its
``after_process_message`` hook runs before the default Retries hook. The last
exception is stored in ``message.options.pg_failure`` with ``type``, ``text``
(maximum 2,000 characters), UTC ``time`` and one-based ``attempt``. It is removed
on success and persisted through the normal enqueue/ack/nack paths. No extra
SQL writes or schema migration are needed. Diagnostic hook failures are logged
by Dramatiq and do not replace the actor exception. Keep this hook after Retries
in middleware registration order when customizing the middleware list.

The CLI ``failed list/show`` displays rejected messages as JSON; ``retry ID``
conditionally requeues a rejected row and clears its stale result. See README
for filters, cursor pagination, payload opt-in and retry-cycle semantics.


Queue statistics
================

``queue_statistics(pool, *, schema="dramatiq", prefix="", queue=None)``
from ``dramatiq_pg.metrics`` returns a list of snapshots containing ``queue``,
``counts`` for queued/consumed/done/rejected, ``ready``, ``scheduled`` and
``oldest_ready_seconds``. It uses a single PostgreSQL statement and does not
require Prometheus. Ready age uses the current enqueue timestamp and ETA;
consumed rows are excluded from ready age. Empty selected queues return zeros.

``PostgresQueueCollector(pool, **options)`` uses the same query and yields
Prometheus gauges with queue/state labels. It imports prometheus_client only
when collecting. Registry registration performs no database access. The caller
owns the pool and should register the collector in a dedicated exporter process.
