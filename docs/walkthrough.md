# Step by step: your first queue

This guide uses the published `0.13.0rc4` release candidate. Tasks and results
are stored in PostgreSQL; a Dramatiq worker runs separately from the producer.

## 1. Prepare PostgreSQL

### Manually

1. Create a database and role using your database administration tool.
2. Grant the application role access to its database and permission to create
   its initial schema. Use your normal deployment roles for production.
3. Configure `PGHOST`, `PGPORT`, `PGUSER`, `PGDATABASE` and credentials in your
   application environment. Do not commit passwords.
4. Use a writable primary with persistent sessions. PgBouncer transaction pooling
   is unsuitable for the broker's session locks/listeners.

### Through commands

For local evaluation, the repository provides an optional PostgreSQL 18 Compose
service. It starts fresh storage, without a partial queue schema:

```sh
git clone https://github.com/wa-pis/iddqueue.git
cd iddqueue
docker compose -f examples/postgres/compose.yml up -d postgres
export PGHOST=127.0.0.1 PGPORT=5432 PGUSER=postgres PGDATABASE=postgres
export PGPASSWORD=postgres
```

The credentials above belong only to the local example. If port 5432 is in use,
adjust the Compose port mapping and `PGPORT`. Prefer a separate deployment
rather than pointing destructive functional tests at an application database.

## 2. Install

### Manually

1. Choose Python 3.10 or newer; the tested matrix is 3.10, 3.13 and 3.14.
2. Create a virtual environment in your application directory.
3. Install the published release candidate with the `binary` extra.
4. Verify that the CLI reports `0.13.0rc4`.

### Through commands

```sh
uv venv
uv pip install "iddqueue[binary]==0.13.0rc4"
uv run --no-sync iddqueue --version
```

The binary extra supplies libpq; base installation requires system libpq.
The optional `monitoring` extra adds Prometheus support.

## 3. Initialize storage

For a **new database/schema**:

```sh
uv run --no-sync iddqueue init
```

For **existing dramatiq-pg/IDDQueue storage**, stop participants, back up and
follow the [migration guide](migration.md), then run `iddqueue upgrade`.
Do not run both commands blindly: `init` creates new storage.
For another storage namespace, put global flags before the command:

```sh
uv run --no-sync iddqueue --schemaname myapp --prefix jobs_ init
```

Configure that same schema/prefix on all brokers/backends/workers/CLI operations.

## 4. Register an actor

Create `tasks.py` manually in your application directory:

```python
import dramatiq
from iddqueue import PostgresBroker

broker = PostgresBroker()
dramatiq.set_broker(broker)

@dramatiq.actor(broker=broker, store_results=True)
def add(left: int, right: int):
    return left + right
```

For a custom namespace, pass `schema="myapp", prefix="jobs_"` to the broker.
Each process creates its own pool; do not share open pools across a fork.

## 5. Start and send

Start the worker in one terminal:

```sh
uv run --no-sync dramatiq --use-spawn --processes=1 --threads=1 tasks
```

In another terminal in the same directory/environment:

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

Expected result: `5`. The timeout is milliseconds; publication does not itself
mean execution has completed. Delivery is at least once, so side effects must
be idempotent. Stop the worker normally with Ctrl+C.

## 6. Inspect and recover

```sh
uv run --no-sync iddqueue stats --json
uv run --no-sync iddqueue failed list --limit 50
uv run --no-sync iddqueue failed show MESSAGE_ID
uv run --no-sync iddqueue retry MESSAGE_ID
```

Replace `MESSAGE_ID` with an actual rejected message UUID. Retry starts a fresh
retry cycle; it does not revive cancelled work. Pause/cancellation requires
`queue_control=True` on every participating worker. Do not use `flush` as a
routine cleanup command: it discards queued/consumed rows.

Continue with [recipes](recipes.md), [FastAPI](fastapi.md),
[deployment/retention](deployment-guide.md) and [CLI/API](api.md).
