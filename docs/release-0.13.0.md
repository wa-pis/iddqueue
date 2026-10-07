# IDDQueue 0.13.0

The first stable IDDQueue release promotes the verified RC5 runtime. No runtime,
dependency or database schema changes are introduced after RC5.

## Highlights

- PostgreSQL broker and Results backend for Dramatiq using Psycopg 3, with lazy
  owned pools, session advisory locks, LISTEN/NOTIFY and delayed tasks.
- Domain actor declarations before broker initialization, domain-derived queue
  names and one application entrypoint for multiple worker processes.
- Atomic business data and task publication through caller-owned synchronous or
  asynchronous Psycopg transactions; optional synchronous SQLAlchemy adapter.
- Deduplication keys/TTL and ordered atomic batches of up to 1000 inputs.
- PostgreSQL rate limits, durable barriers and standard Dramatiq group callbacks;
  verified pipelines, groups and AsyncIO middleware.
- Failed-task inspection/retry, queue pause/resume, cooperative cancellation,
  opt-in attempt history and a fixed-interval scheduler.
- Queue/domain statistics, native error/retry metrics and optional Prometheus
  collection with a Grafana example.
- External schema management, custom recipes, FastAPI examples and graceful
  worker shutdown/restart guides.

These capabilities were delivered and tested across RC1–RC5. This release adds
stable packaging and documentation rather than new runtime behavior.

## Install and upgrade

```bash
uv pip install "iddqueue[binary]==0.13.0"
```

From **0.13.0rc5**, update the package pin; no DDL migration or actor changes are
required. Roll back by restoring the RC5 pin. From older IDDQueue candidates or
upstream dramatiq-pg, follow the [migration guide](migration.md), including backup,
explicit schema upgrade where required and rollback validation. The broker never
creates or migrates database objects automatically.

See [domain setup](domains.md), [async transactional recipe](recipes.md#async-transactional-publishing),
[SQLAlchemy](sqlalchemy.md) and [API reference](api.md).

## Operational boundaries

Delivery remains **at least once**; actors must be idempotent. Deduplication does
not provide exactly-once execution. Locks/listeners require persistent PostgreSQL
sessions, so PgBouncer transaction pooling is unsuitable. Namespaces separate
storage; they do not enforce access control.

Async transaction methods accept an active caller-owned Psycopg AsyncConnection
in the same database as the business writes. Enqueue hooks remain synchronous and
pre-commit. Ordinary publication, consumers, results and the SQLAlchemy adapter
remain synchronous. Scheduling supports fixed intervals, not cron expressions.

IDDQueue remains pre-1.0: extension API stability follows the
[support policy](https://github.com/wa-pis/iddqueue/blob/main/SUPPORT.md).
The tested CI matrix is Python 3.10/3.13/3.14 × PostgreSQL 14/18; other versions
are not implied by broad dependency ranges. The archived django-dramatiq-pg
integration has not been validated with IDDQueue.

## Verification and attribution

The release gate checks unit/functional tests on a dedicated PostgreSQL instance,
Ruff, locked dependencies, strict documentation/OpenSpec, wheel/sdist LICENSE,
isolated installation profiles, quickstart and the async business/actor recipe.
Local validation passed: **200 tests**, async actor recipe, strict docs/OpenSpec,
build/LICENSE and isolated base/monitoring/SQLAlchemy profiles. All six candidate
CI combinations must pass before publication. GitHub and PyPI
receive the same verified artifacts with SHA256 readback and a clean registry install.

The completed static Codex Security diff review after RC4 covered 20 changed paths
and found no new security findings. This is not a fresh full-repository or
production deployment audit. See the [changelog](https://github.com/wa-pis/iddqueue/blob/main/CHANGELOG.md)
and [release procedure](release.md).

IDDQueue preserves DALIBO's PostgreSQL license and original contributor credits.
