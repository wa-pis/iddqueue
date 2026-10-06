# IDDQueue

[Documentation](https://wa-pis.github.io/iddqueue/) · [Step-by-step setup](https://wa-pis.github.io/iddqueue/walkthrough/)

A PostgreSQL broker and Results backend for [Dramatiq](https://dramatiq.io/),
built on synchronous Psycopg 3. Tasks, results and coordination live in PostgreSQL;
no Redis or ORM is required by IDDQueue.

**Current release: [0.13.0rc2](https://pypi.org/project/iddqueue/0.13.0rc2/)** —
a release candidate for evaluation. [GitHub assets](https://github.com/wa-pis/iddqueue/releases/tag/v0.13.0rc2)
include the wheel, sdist and SHA256 checksums.

IDDQueue is a fork of [DALIBO's dramatiq-pg](https://gitlab.com/dalibo/dramatiq-pg)
([original package](https://pypi.org/project/dramatiq-pg/)). It preserves the
PostgreSQL license and original contributor credits.

## What it provides

- Durable JSONB task/results storage, delayed tasks and crash recovery.
- Transactional publication alongside business writes; atomic batches and deduplication.
- PostgreSQL rate limiters, barriers and Dramatiq group callbacks.
- Pause/resume, cooperative cancellation, failed-task inspection/retry and attempt history.
- Fixed-interval scheduling and optional Prometheus queue metrics.
- Schema/prefix isolation and a [tested FastAPI example](docs/fastapi.md).

Delivery is **at least once**: actors and callbacks must be idempotent.
LISTEN/NOTIFY carries message IDs as wakeup hints; consumers claim authoritative
SQL rows with session advisory locks. See [behavior and limits](docs/user-guide.md).

## Install

Requires Python 3.10+, Dramatiq 2.2.1+ and Psycopg 3.3.6+.
CI tests Python **3.10 / 3.13 / 3.14** with PostgreSQL **14 / 18**.
See [compatibility and API stability](SUPPORT.md).

```sh
uv venv
uv pip install "iddqueue[binary]==0.13.0rc2"
```

The `binary` extra supplies libpq. Base installs require system libpq;
`[binary,monitoring]` also enables Prometheus support.

**Migrating from dramatiq-pg?** Follow the [migration guide](docs/migration.md)
before changing imports, pools or database storage. Stop all participants,
back up data, run the upgrade and restart consistently. Fresh initialization
and an existing-storage upgrade are different operations.

## Quickstart

Configure PostgreSQL using `PGHOST`, `PGPORT`, `PGUSER`, `PGDATABASE` and your
normal credential mechanism. Initialize fresh storage:

```sh
uv run --no-sync iddqueue init
```

For existing storage, use `iddqueue upgrade` after following the migration guide.
Both commands manage the complete feature schema.

Save as `tasks.py`:

```python
import dramatiq
from iddqueue import PostgresBroker

broker = PostgresBroker()
dramatiq.set_broker(broker)

@dramatiq.actor(broker=broker, store_results=True)
def add(left: int, right: int):
    return left + right
```

Start a separate worker from the same directory/environment:

```sh
uv run --no-sync dramatiq --use-spawn --processes=1 --threads=1 tasks
```

In another terminal, publish and read the result:

```sh
uv run --no-sync python - <<'PY'
from tasks import add, broker

try:
    message = add.send(2, 3)
    print(message.message_id)
    print(message.get_result(backend=broker.backend, block=True, timeout=10000))
finally:
    broker.close()
PY
```

The result is `5`; timeouts are milliseconds. Each process creates its own pool.
Close broker-owned pools on shutdown; callers close pools they supply.

## Guides and examples

- [Documentation index](docs/index.md), [user guide](docs/user-guide.md), [API](docs/api.md).
- [Detailed recipes](docs/recipes.md): transactions, middleware, controls, metrics and schedules.
- [FastAPI](docs/fastapi.md): lifespan, async endpoint thread offload and separate worker.
- [Deployment and retention](docs/deployment-guide.md), [why PostgreSQL](docs/why.md).
- [RC notes](docs/rc-0.13.0rc2.md), [changelog](CHANGELOG.md), [release checks](docs/release.md).

The broker and result APIs are synchronous. Async actors use Dramatiq's AsyncIO
middleware; FastAPI async endpoints offload publication to a thread.
Transactional enqueue does not accept a Psycopg AsyncConnection.

Session-bound locks/listeners require persistent database sessions; PgBouncer
transaction pooling is unsuitable. Namespace separation is not access control.
The legacy [django-dramatiq-pg](https://github.com/uptick/django-dramatiq-pg/)
integration has been archived since September 3, 2024; IDDQueue compatibility
is unverified. No tested Django integration is currently provided.

## Compared with dramatiq-pg

Baseline: [dramatiq-pg 0.12.0](https://pypi.org/project/dramatiq-pg/0.12.0/),
compared with the published IDDQueue 0.13.0rc2 prerelease. This describes the published version, not every
future upstream revision. Both projects provide a PostgreSQL Dramatiq broker.

| Area | dramatiq-pg 0.12.0 | IDDQueue 0.13.0rc2 / practical benefit |
| --- | --- | --- |
| Core storage and delivery | JSONB tasks/results, delayed tasks, LISTEN/NOTIFY, advisory locks, recovery and maintenance CLI | Preserved; at-least-once delivery still requires idempotent actors |
| Runtime | Python >=3.6,<4; Dramatiq >=1.5,<2; Psycopg 2 | Python >=3.10,<4; Dramatiq >=2.2.1,<3; synchronous Psycopg 3 and psycopg-pool |
| Pool lifecycle | Psycopg 2 pools | Lazy owned pools, explicit close, caller-owned pool support |
| Transactional publication | Regular enqueue | Caller-owned transaction API: commit business data and tasks together |
| Coordination | No PostgreSQL rate-limit/barrier backend | PostgreSQL rate limits, durable barriers and standard GroupCallbacks without Redis |
| Task operations | stats, purge, recover, flush | Failed-task inspection/targeted retry, pause/resume, cooperative cancellation and opt-in attempt history |
| Publication controls | Single-message enqueue | Deduplication keys/TTL and atomic batches of up to 1000; deduplication is not exactly-once execution |
| Scheduling | Per-message delay | Also a multi-process fixed-interval scheduler; no cron/calendar expressions |
| Observability | Basic CLI statistics | Ready/scheduled backlog, task age and optional Prometheus collector |
| Storage namespaces | Configurable schema/table prefix; shared channel/lock domains | Instance-specific queries and schema/prefix-specific channels/locks; storage separation is not access control |
| Dramatiq integration | Broker/results implementation | Verified pipelines, groups, AsyncIO and standard middleware; these are Dramatiq features, not a replacement orchestration engine |
| Compatibility evidence | Historical upstream tests | CI on Python 3.10/3.13/3.14 × PostgreSQL 14/18, functional tests and installed-wheel checks |

See [migration from dramatiq-pg](docs/migration.md) for dependency, pool,
import, CLI and database changes, including backup and rollback. No throughput
advantage is claimed here. The 0.13.0rc2 prerelease is available on PyPI; the legacy Django
integration is archived and has not been verified with IDDQueue.

## Development and support

Use [CONTRIBUTING](CONTRIBUTING.md) for locked uv setup and the full release gate.
Functional tests require a dedicated PostgreSQL instance: they terminate sessions
and crash/restart workers. Project planning and evidence live in
[OpenSpec](openspec/roadmap.md). Report reproducible issues on
[GitHub](https://github.com/wa-pis/iddqueue/issues).

## License and credits

Released under the [PostgreSQL license](LICENSE), preserving
`Copyright (c) 2019, DALIBO` and the original author Étienne BERSAC.

Thanks to upstream contributors Andy Freeland, Curtis Maloney (Django support),
Federico Caselli, Giuseppe Papallo and Rafal Kwasny. The historical upstream logo
was created by [Damien CAZEILS](http://www.damiencazeils.com/).
[Original changelog](docs/changelog.rst) remains available as historical context.
