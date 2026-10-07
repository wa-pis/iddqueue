# FastAPI integration

IDDQueue works with FastAPI using its synchronous Psycopg 3 broker. The runnable
[web example](https://github.com/wa-pis/iddqueue/blob/main/examples/fastapi/app.py) publishes from an async endpoint through
`await asyncio.to_thread(actor.send, ...)`; the event loop remains available.
[Shared actors](https://github.com/wa-pis/iddqueue/blob/main/examples/fastapi/tasks.py) are registered on an explicit broker.
The [worker entry point](https://github.com/wa-pis/iddqueue/blob/main/examples/fastapi/worker.py) runs separately.

## Run from a checkout

Install the locked example group (FastAPI, HTTPX and Uvicorn are not IDDQueue
runtime dependencies):

```sh
uv sync --locked --extra binary --group fastapi-example
```

Configure PostgreSQL using libpq environment variables (`PGHOST`, `PGPORT`,
`PGUSER`, `PGDATABASE`, and credentials supplied by your environment), or
`IDDQUEUE_DATABASE_URL`. Do not put credentials in source control. The default
schema is `dramatiq`; set `IDDQUEUE_SCHEMA` for another schema. Initialize once,
before starting either process, using the same connection and schema:

```sh
uv run --no-sync python -c 'from iddqueue import generate_init_sql; import psycopg; import os; conn = psycopg.connect(os.getenv("IDDQUEUE_DATABASE_URL", ""), autocommit=True); conn.execute(generate_init_sql(os.getenv("IDDQUEUE_SCHEMA", "dramatiq"))); conn.close()'
```

In separate terminals, with the same environment and working directory:

```sh
uv run --no-sync dramatiq --use-spawn --processes=1 --threads=1 examples.fastapi.worker
uv run --no-sync uvicorn examples.fastapi.app:app
```

```sh
curl -i http://127.0.0.1:8000/tasks -H 'Content-Type: application/json' -d '{"a":2,"b":3}'
```

HTTP 202 returns `message_id` after `.send()` succeeds. It confirms publication,
not completion; the worker computes and stores `5`. Publication failure returns
503 without SQL/connection details. The example validates the request body and
has no result polling or queue administration endpoint.

## Lifespan and synchronous endpoints

The web broker is created in FastAPI lifespan, once per application process, and
closed on shutdown, including when actor registration or the lifespan body fails.
Creation and closing run in a thread. Importing the web app opens no pool.
Each spawned Dramatiq worker creates its own broker; no open web pool crosses
process boundaries. Do not run Dramatiq workers inside HTTP request handlers.

For a normal `def` endpoint, FastAPI already runs the handler in a threadpool,
so `.send()` can be called directly:

```python
@app.post("/tasks-sync", status_code=202)
def enqueue_sync(body: Addition, request: Request):
    message = request.app.state.add.send(body.a, body.b)
    return {"message_id": message.message_id}
```

Keep the same publication error handling as the runnable async example. A direct
`.send()` inside `async def` blocks the event loop. Likewise, blocking result
retrieval must run in a thread; do not wait for results in this example's endpoint.
FastAPI `BackgroundTasks` is not a durable replacement for publication before
returning 202.

The example uses the broker's default pool. Account for the total connection
budget across web and worker processes. For explicit pool limits, construct a
Psycopg `ConnectionPool` with `open=False` and `kwargs={"autocommit": True}`, pass it as `PostgresBroker(pool=pool)`,
and close that pool yourself in lifespan: an injected pool belongs to you.

## Transactions and retries

Delivery remains at least once. Actors with side effects must be idempotent.
Request cancellation/disconnection does not stop a running publication thread;
a commit may have succeeded even if the client received no response. Retrying
that HTTP request may enqueue another message; no exactly-once promise is made.

Synchronous [transactional enqueue](user-guide.md) uses a Psycopg
Connection: move the whole business transaction into a thread if using that API. Sending through
an independent pool is not atomic with your application's transaction.

RC5 provides `await broker.enqueue_in_transaction_async(...)`
and `await broker.enqueue_many_in_transaction_async(...)` on an active caller-owned
Psycopg AsyncConnection. Business writes and publication use that same connection;
commit exposes both and rollback cancels both. See the framework-independent
[async transaction recipe](recipes.md#async-transactional-publishing).
These explicit methods perform async DB I/O. SQLAlchemy async inputs remain
unsupported by the optional adapter.

Async actors remain available through Dramatiq's AsyncIO middleware; that does
not make PostgreSQL publication or result retrieval asynchronous.

## Verification

The release gate installs the example group and runs lifecycle/error/event-loop
tests plus HTTP → PostgreSQL → separate worker acceptance. Functional tests
require a dedicated PostgreSQL instance and create/drop an isolated schema.
The existing Python/PostgreSQL CI matrix also runs these tests.

References: [FastAPI lifespan](https://fastapi.tiangolo.com/advanced/events/),
[sync and async endpoints](https://fastapi.tiangolo.com/async/),
[async testing](https://fastapi.tiangolo.com/advanced/async-tests/).
