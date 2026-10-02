Dramatiq-pg Changelog
=====================

Unreleased
----------

- Add per-queue ready/scheduled backlog and optional PostgreSQL Prometheus metrics.
- Reset enqueue timestamps when requeuing a new attempt.

- Add last-error metadata, paginated failed-task inspection and targeted retry.

- Verify pipelines, groups, AsyncIO actors, retry exhaustion callbacks and timedelta delays against PostgreSQL.

- Add PostgreSQL rate limits, durable barriers and standard GroupCallbacks support.
- Add an idempotent coordination-table migration and expiry cleanup.
- Add enqueue_in_transaction for atomic publication with application data.

- Require Python 3.10+, Dramatiq 2.2.1+ and Psycopg 3.3.6+.
- Replace psycopg2 pools with lazy Psycopg 3 connection pools.
- Preserve pooled sessions when committing and rolling back transactions.
- Release consumer subscriptions and advisory locks on shutdown.
- Isolate SQL configuration between broker and result-backend instances.
- Respect result TTL and millisecond timeouts; support large result payloads.
- Use timezone-aware timestamps and remove obsolete WITHOUT OIDS syntax.
- Add GitHub Actions testing against PostgreSQL 14 and 18.
- Workaround payloads bigger than 8Kb


Version 0.11
------------

Released 2021-11-19.

- Add new --schemaname argument to CLI. Reported by `@davidolrik`_.
- Use Dramatiq customizable encoder.
- Enhance reliability: configure keepalives, retry on error, cooperate with
  Dramatiq self-healing and more.
- Set libpq ``application_name``.


Version 0.10
------------

Released 2021-04-27.

- Fix duplicate execution of delayed message. Reported by `@rmcgover`_ and
  `@liveFreeOrCode`_.
- Fix retrying of message with Retries middleware. Reported by `@liveFreeOrCode`_.
- Emit ``enqueue`` event. By `@liveFreeOrCode`_.


Version 0.9.0
-------------

Released 2020-10-02.

- Allow to customize schema and table names.
- Provide ``dramatiq-pg init`` helper command.
- Correctly clear the advisory locks. Contribution from `@CaselIT`_.
- Use loose constraint on tenacity. By `@rouge8`_.


Version 0.8.0
-------------

- Fix typo.


Version 0.7.1
-------------

Released 2019-11-12.

- Fix polling when idle. Patch from Daniel.


Version 0.7.0
-------------

Release 2019-11-04.

- Respect prefetch from Dramatiq, improving cooperation between workers.
  Contribution from @mag.
- Automatic recovery of message after crash. You don't need to manually requeue
  anymore.
- More reliability: connection lost are handled everywhere, retrying on network
  failure is enabled.
- Allows to use psycopg[binary] wheel. You must install psycopg or
  psycopg[binary] yourself.
- By default, connection pool tries to reuse all connections.
- Configure connection string of CLI.
- dramatiq.queue table definition has been reviewed for optimisation. Changes
  are not required.


Version 0.5.0
-------------

Released 2019-04-04.

This release requires an update of the schema.

- Stores result in Database. This is enabled by default.
- Flush all queues from CLI.
- Documentation user guide, deployment, the why.
- Add performance metric tools.


Version 0.4.0
-------------

Released 2019-03-13.

-  Fixed blocking consumer thread. ``select`` syscall is now called
   every seconds by default.
-  Removed automatic recovery on startup. This break multi-worker
   process on same queue with long running task. You need to manually
   requeue messages after a crash.
-  Added delayed task support.
-  Added documentation on deployment constaints and limitations.
-  Added manual requeue from CLI tool.
-  Added URL parameter to PostgresBroker constructor.
-  Reuse listening connexion to purge message table. This reduce slighly
   connexion usage.


Version 0.3.0
-------------

Released 2019-03-07.

-  Added rejecting message (nack).
-  Added message replay from table at startup. Missed NOTIFY are not
   lost anymore.
-  Requeue old consumed message on startup. Recover from crashed
   process.
-  Added CLI tool to manually purge queue and show some stats.
-  Added random periodic purge of message table.
-  Use BIGSERIAL on message table.
-  Added index on message table to fasten purge and stats.
-  Added projet licence, logo and metadata.


Version 0.2.0
-------------

Released 2019-02-22.

-  First working implementation.
-  Added func tests.

.. _@CaselIT: https://gitlab.com/CaselIT
.. _@davidolrik: https://gitlab.com/davidolrik
.. _@liveFreeOrCode: https://gitlab.com/liveFreeOrCode
.. _@rmcgover: https://gitlab.com/rmcgover
.. _@rouge8: https://gitlab.com/rouge8
