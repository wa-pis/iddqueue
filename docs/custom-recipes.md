# Write your own recipe

A recipe is a small, reproducible application example: one task, its bootstrap,
commands to run it, and an expected result. Start with existing [recipes](recipes.md)
and extend the closest one. Domain actors below are available in published
**0.13.0rc3**. The newer SQLAlchemy adapter and domain monitoring are currently
[development features](sqlalchemy.md), not part of that release.

## 1. Define the contract

Write down the input, result, destination domain, side effects and failure policy.
For example: `billing.add(2, 3)` returns `5`, uses queue `billing`, and has no
external side effects. Pass JSON-compatible values such as IDs and strings;
load application records inside the actor. Avoid passing sessions, connections
or credentials as task arguments.

For business operations, decide how repeated execution is handled before writing
code. Delivery is at least once: a worker can complete a side effect and crash
before acknowledgment. Enqueue deduplication does not make execution exactly once.
Use a business key and a database constraint or an external API's idempotency key.

## 2. Separate tasks from bootstrap

Create this structure in your application directory:

```text
myrecipe/
    __init__.py
    tasks.py
    worker.py
    producer.py
```

Leave `__init__.py` empty. Define actors in `myrecipe/tasks.py`:

```python
from iddqueue import Domain

billing = Domain("billing")


@billing.actor(store_results=True, max_retries=3)
def add(left, right):
    return left + right
```

Importing this module does not connect to PostgreSQL or initialize a default
broker. Domain supplies both the actor name `billing.add` and queue `billing`.
Do not send messages before registration.

Put initialization in `myrecipe/worker.py`:

```python
import os

import dramatiq
from iddqueue import PostgresBroker

from .tasks import billing

broker = PostgresBroker(url=os.environ["DATABASE_URL"])
dramatiq.set_broker(broker)
billing.register(broker)
```

Each producer and worker process needs its own bootstrap and pool. Register all
its domains against the same broker before sending or starting consumption.
Task modules must not import `worker`: that would recreate the import cycle.
Add middleware before registering domains when using extra actor options.
See [Domain actors](domains.md) for multiple domains, workers and Docker.

Create `myrecipe/producer.py`:

```python
from .worker import broker
from .tasks import add


def main():
    try:
        message = add.send(2, 3)
        result = message.get_result(
            backend=broker.backend, block=True, timeout=10_000,
        )
        assert result == 5, result
        print(result)
    finally:
        broker.close()


if __name__ == "__main__":
    main()
```

Results must be enabled on actors whose output you retrieve. The timeout is in
milliseconds; a timeout does not cancel the queued task. Importing the producer
alone does not send a message.

## 3. Run manually or with commands

Manually: create a virtual environment, install the published binary extra,
configure a dedicated test database, initialize its storage, start a worker in
one terminal, and run the producer in another. Expect `5`. Stop the worker with
Ctrl+C after the producer finishes.

Equivalent commands, run from the directory containing `myrecipe/`:

```sh
uv venv
uv pip install 'iddqueue[binary]==0.13.0rc3'
export DATABASE_URL='postgresql://localhost/recipe_test'
# CLI uses PostgreSQL's standard environment variables.
export PGHOST=localhost PGDATABASE=recipe_test
# Set PGUSER, PGPORT and PGPASSWORD as required by your database.
uv run --no-project iddqueue init
uv run --no-project dramatiq myrecipe.worker --processes 1 --threads 2 --queues billing
```

In the second terminal, use the same directory and DATABASE_URL:

```sh
export DATABASE_URL='postgresql://localhost/recipe_test'
uv run --no-project python -m myrecipe.producer
```

Create `recipe_test` first using your database administration tool. Adjust both
the DSN and PG variables together: worker, producer and CLI must target the same
database, schema and prefix. `init` is for fresh storage; use `upgrade` for a
supported existing installation. For application-owned DDL, follow
[external schema management](migration.md#manage-schema-through-application-migrations).
Bootstrap does not run migrations.

## 4. Extend one behavior at a time

| Need | Reuse | Check |
| --- | --- | --- |
| Business update and enqueue atomically | [Transactional publishing](recipes.md#transactional-publishing) | Commit exposes both; rollback exposes neither |
| Ordered steps or parallel work | [Pipelines and groups](recipes.md#standard-dramatiq-composition-and-middleware) | Results and failure behavior, including different domain queues |
| Async actor | Standard `AsyncIO` middleware in bootstrap | Blocking database work stays outside the event loop |
| Retries and diagnosis | [Failed task inspection](recipes.md#inspect-and-retry-failed-tasks) | Retry budget, terminal failure and safe repeated side effects |
| Monitoring | [Debugging metrics](debugging.md) | Errors/retries, backlog age, duration; no task IDs as labels |
| Framework integration | [FastAPI example](fastapi.md) | Producer bootstrap in every application process |

Pipelines across domains require workers consuming every destination queue.
The default retry policy applies only when errors reach Dramatiq: do not swallow
an exception and report success. A retry budget is not a timeout or cancellation
policy. See the [user guide](user-guide.md) for those controls.

## 5. Make the recipe reviewable

Include prerequisites and package version, file contents, exact startup commands,
expected output and shutdown/cleanup steps. Record which commands you actually
ran. Distinguish published features from development-only ones.

Test the success path, a terminal error, and repeated delivery. For transactional
recipes, verify commit and rollback. For multiple domains, verify routing with a
worker consuming only the intended queue. Check that shutdown closes owned pools;
do not close a pool supplied by the application while other users still need it.

Use dedicated PostgreSQL for repository functional tests: they terminate database
connections and restart workers. To contribute a recipe, add its guide under
`docs/`, reusable runnable files under `examples/` when needed, link it from
this site's navigation, and follow [CONTRIBUTING](https://github.com/wa-pis/iddqueue/blob/main/CONTRIBUTING.md).
Keep secrets out of checked-in commands and output. Remove only storage created
for your recipe after stopping its processes; never use a production database
for destructive test cleanup.
