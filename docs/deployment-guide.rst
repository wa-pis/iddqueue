================
Deployment Guide
================

Connections
===========

Use a writable PostgreSQL primary. LISTEN/NOTIFY and session advisory locks
require persistent sessions: PgBouncer transaction pooling is unsuitable;
use session pooling if deployed. Notifications are wakeup hints and are not
replicated. Keep broker pools separate from business transactions, and create
pools after process creation rather than sharing open pools across fork.

Each consumer retains two connections (listener and claim/locks). Count normal
and delayed consumers. Add concurrent ACK/result/producer operations and any
scheduler/exporter connections. Sum all per-process pool limits and business
connections when setting PostgreSQL max_connections. URL maxconn defaults to 16;
measure actual workload and keep capacity headroom. Close broker-created pools
on shutdown; callers close supplied pools.

Upgrades
========

Back up storage, stop producers, gracefully stop workers, result waiters and
schedulers, then run the matching namespace upgrade::

    iddqueue --schemaname myapp --prefix jobs_ upgrade

Restart all participants together with matching schema/prefix and queue_control
configuration. Version 0.13 uses Psycopg 3 pools and the iddqueue import/CLI names.
Non-default areas and long queue names use bounded notification channels and
namespace-aware locks; mixed old/new processes can miss wakeups or share locks
incorrectly. Persisted UUIDs and queue rows remain in place. Do not drop storage
to upgrade. The migration adds enum values/columns and tables: rolling back code
alone does not reverse DDL; restore a compatible backup or plan an explicit
migration after stopping participants. See `support policy <../SUPPORT.md>`_.

Operations
==========

Global --dsn, --schemaname and --prefix flags precede commands. The CLI also
reads libpq PG* environment variables. Start with help and snapshots::

    iddqueue --help
    iddqueue stats --json
    iddqueue failed list --limit 50
    iddqueue failed show MESSAGE_ID
    iddqueue retry MESSAGE_ID
    iddqueue queue-status emails

Monitor ready/scheduled counts, oldest_ready_seconds, rejected/cancelled rows,
DB connections, storage size and autovacuum. Install the monitoring extra and
register PostgresQueueCollector in a separate exporter for SQL queue gauges;
Dramatiq's built-in execution metrics are a separate surface. Large retained
payloads increase aggregation cost; measure scrape frequency and retention.

Crash recovery is at least once. Session loss releases locks, restart scans
queued/abandoned messages, and idle consumers occasionally scan storage. The
idle recovery scan is probabilistic, not a five-minute SLA. Notifications may
be stale or absent; claims read authoritative rows and enforce consumer queue.
Make actor side effects idempotent and choose a service manager restart policy.

Retention and maintenance
=========================

``iddqueue purge --maxage '30 days'`` removes old terminal queue rows, including
Results and cancellation markers. Consumers occasionally purge with a 30-day
policy when idle; there is no deterministic daily cleanup guarantee. Queue
purge does not remove live dedup keys, schedules or attempt history.
Schedule explicit maintenance for predictable retention::

    iddqueue history purge --maxage '30 days'
    iddqueue schedule list
    iddqueue schedule disable reports

Purge expired coordination rows through PostgresRateLimiterBackend.purge().
Delete deduplication rows only after expires_at <= clock_timestamp(); they retain
the original message payload. History retention uses start time and may remove
old incomplete records. Disabled schedules remain stored. Configure autovacuum
and monitor bloat; retain terminal rows long enough for Results readers.

``iddqueue flush`` deletes queued/consumed tasks, including active work's rows;
use only when intentionally discarding tasks. ``recover --minage '1 min'`` resets
old consumed state but cannot interrupt a live actor or bypass its session lock;
cancelled rows remain terminal. Pausing stops new actor starts, not running work;
cancellation of running work requires actor cooperation. Schedule operations
publish without importing actors, so workers must register every scheduled actor.
