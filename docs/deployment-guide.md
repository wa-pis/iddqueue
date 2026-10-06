# Deployment Guide

## Connections

Use a writable PostgreSQL primary. LISTEN/NOTIFY and session advisory locks require persistent sessions: PgBouncer transaction pooling is unsuitable; use session pooling if deployed. Notifications are wakeup hints and are not replicated. Keep broker pools separate from business transactions, and create pools after process creation rather than sharing open pools across fork.

Each consumer retains two connections (listener and claim/locks). Count normal and delayed consumers. Add concurrent ACK/result/producer operations and any scheduler/exporter connections. Sum all per-process pool limits and business connections when setting PostgreSQL max_connections. URL maxconn defaults to 16; measure actual workload and keep capacity headroom. Close broker-created pools on shutdown; callers close supplied pools.

## Graceful restart and shutdown

Use the standard Dramatiq supervisor. On Unix, send **SIGTERM** (or Ctrl+C /
SIGINT) to stop, and **SIGHUP** to reload worker processes. Send signals to the
supervisor, not individual child processes. During shutdown workers stop taking
new work, wait for active actors within the configured budget, and requeue
remaining prefetched work. Broker-owned pools close during worker exit.

For example, run from the application directory with its database settings:

```sh
dramatiq myrecipe.worker --processes 2 --threads 4 --worker-shutdown-timeout 120000 &
worker_pid=$!
# Reload after code/settings available to the process have changed:
kill -HUP "$worker_pid"
# Later, stop and wait for the supervisor:
kill -TERM "$worker_pid"
wait "$worker_pid"
```

The shutdown timeout is in **milliseconds**; Dramatiq 2.2.1 defaults to
600000 (ten minutes). The example uses two minutes, not a universal recommended
limit. Choose a budget longer than your expected actor completion and cleanup.
A reload starts new process-local brokers and pools. Pending messages stay in
PostgreSQL, so stop/restart is also available if SIGHUP is unsupported.

For Docker keep the exec-form CMD used by the
[domain example](https://github.com/wa-pis/iddqueue/blob/main/examples/domains/Dockerfile)
so the supervisor receives signals. Allow the container more time than the
worker shutdown budget:

```sh
# Existing container named iddqueue-worker, configured with the 120000ms budget:
docker stop --time 150 iddqueue-worker
# Reload the running supervisor instead:
docker kill --signal=HUP iddqueue-worker
```

These are alternative actions: HUP requires a running container. In Compose set
`stop_grace_period: 150s` on the worker service. Keep the same principle for your
service manager: deliver SIGTERM and wait before forcing termination. To deploy
an immutable new image, gracefully stop/replace a replica and start its
replacement; SIGHUP alone does not install another image. Multiple replicas can
keep processing while one restarts. Database upgrades still require the
[coordinated procedure below](#upgrades).

A second termination signal or an expired container/service-manager grace period
can force interruption. Arbitrary blocking actor I/O is not guaranteed to finish
within the budget. After interruption a task may run again; make side effects
idempotent. Graceful shutdown does not mean flushing/deleting the queue. Callers
remain responsible for pools they supply, and for stopping their own producers,
exporters and schedulers. Native Prometheus multiprocess files need a replica
lifecycle policy after a hard kill; see [debugging](debugging.md).

An installed development-wheel acceptance check on PostgreSQL 14 verifies eight
tasks spanning SIGHUP and an active three-second task spanning SIGTERM, with
results preserved and no remaining application database sessions. This is a
bounded lifecycle check, not an exactly-once guarantee or a test of every service
manager's termination policy.

## Upgrades

Back up storage, stop producers, gracefully stop workers, result waiters and schedulers, then run the matching namespace upgrade:

    iddqueue --schemaname myapp --prefix jobs_ upgrade

Restart all participants together with matching schema/prefix and queue_control configuration. Version 0.13 uses Psycopg 3 pools and the iddqueue import/CLI names. Non-default areas and long queue names use bounded notification channels and namespace-aware locks; mixed old/new processes can miss wakeups or share locks incorrectly. Persisted UUIDs and queue rows remain in place. Do not drop storage to upgrade. The migration adds enum values/columns and tables: rolling back code alone does not reverse DDL; restore a compatible backup or plan an explicit migration after stopping participants. See [support policy](https://github.com/wa-pis/iddqueue/blob/main/SUPPORT.md).

## Operations

Global --dsn, --schemaname and --prefix flags precede commands. The CLI also reads libpq PG\* environment variables. Start with help and snapshots:

    iddqueue --help
    iddqueue stats --json
    iddqueue failed list --limit 50
    iddqueue failed show MESSAGE_ID
    iddqueue retry MESSAGE_ID
    iddqueue queue-status emails

Monitor ready/scheduled counts, oldest_ready_seconds, rejected/cancelled rows, DB connections, storage size and autovacuum. Install the monitoring extra and register PostgresQueueCollector in a separate exporter for SQL queue gauges; Dramatiq's built-in execution metrics are a separate surface. Large retained payloads increase aggregation cost; measure scrape frequency and retention.

Crash recovery is at least once. Session loss releases locks, restart scans queued/abandoned messages, and idle consumers occasionally scan storage. The idle recovery scan is probabilistic, not a five-minute SLA. Notifications may be stale or absent; claims read authoritative rows and enforce consumer queue. Make actor side effects idempotent and choose a service manager restart policy.

## Retention and maintenance

`iddqueue purge --maxage '30 days'` removes old terminal queue rows, including Results and cancellation markers. Consumers occasionally purge with a 30-day policy when idle; there is no deterministic daily cleanup guarantee. Queue purge does not remove live dedup keys, schedules or attempt history. Schedule explicit maintenance for predictable retention:

    iddqueue history purge --maxage '30 days'
    iddqueue schedule list
    iddqueue schedule disable reports

Purge expired coordination rows through PostgresRateLimiterBackend.purge(). Delete deduplication rows only after expires_at \<= clock_timestamp(); they retain the original message payload. History retention uses start time and may remove old incomplete records. Disabled schedules remain stored. Configure autovacuum and monitor bloat; retain terminal rows long enough for Results readers.

`iddqueue flush` deletes queued/consumed tasks, including active work's rows; use only when intentionally discarding tasks. `recover --minage '1 min'` resets old consumed state but cannot interrupt a live actor or bypass its session lock; cancelled rows remain terminal. Pausing stops new actor starts, not running work; cancellation of running work requires actor cooperation. Schedule operations publish without importing actors, so workers must register every scheduled actor.
