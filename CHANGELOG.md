# Changelog

User-facing IDDQueue changes. [Historical upstream releases](docs/changelog.rst)
remain preserved with upstream credits. Unreleased entries are not publication.

## 0.13.0rc2 — release candidate — 2026-10-06

- Publish searchable documentation with step-by-step manual and CLI guides.
- Refresh migration/API/upstream comparison documentation.
- Move test actors and PostgreSQL Compose out of the repository root; remove agent skills from Git.
- Remove unused Dramatiq watch extra and redundant argparse defaults.

- Remove obsolete Poetry test runner, unused upstream logo files and stale tooling configs; use the uv release gate.
- Optional development Compose starts fresh PostgreSQL; initialize complete storage with `iddqueue init` and prepare functional-test schema explicitly.

## 0.13.0rc1 — release candidate — published 2026-10-05

- Send only message IDs in enqueue/ACK/NACK notifications to prevent task-payload disclosure to other database roles. Update all publishers/workers; no DDL change.

### Added

- Runnable FastAPI lifespan/async publication example with a separate worker and PostgreSQL acceptance tests.

- PostgreSQL transactional enqueue and atomic batches (up to 1000 messages).
- PostgreSQL rate limiters, barriers and group completion callbacks.
- Publication deduplication with queue-scoped keys and millisecond TTLs.
- Opt-in pause/resume, cancellation before start and cooperative requests.
- Failed-task inspection/retry CLI, SQL queue statistics and optional Prometheus.
- Opt-in attempt history and retention CLI; fixed interval PostgreSQL scheduler.
- Storage isolation through schema/prefix, including Results and notifications.

### Changed

- Distribution, imports and CLI are named `iddqueue`.
- Synchronous Psycopg 3 pools and Dramatiq 2.2.1+; pools open lazily.

### Fixed

- Consumers use authoritative stored payloads, enforce queue ownership and skip
  stale/deleted notification hints; ACK/NACK locks drain with continuous backlog.

### Deprecated

None.

### Removed

Psycopg 2 pool support.

### Migration

- Update imports/CLI and `iddqueue_queue_` metric names; close owned pools on shutdown.
- Stop participants, back up storage and run `iddqueue upgrade` for optional
  tables/cancellation columns; raw schema.sql alone is incomplete.
- Restart all participants together for non-default namespace/long-channel changes.
- Enable queue_control on every worker using pause/cancellation; enable history
  explicitly. Delivery remains at least once; actors must be idempotent.

Keep entries under Added/Changed/Fixed/Deprecated/Removed/Migration, describing
user behavior and required actions. Add Security only for actual security fixes.
Do not list CI/OpenSpec bookkeeping as user changes. When releasing, move agreed
entries to a version/date section; the release itself requires separate authorization.
