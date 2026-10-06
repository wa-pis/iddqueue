# Domain actors and one bootstrap

This additive API is available in the development checkout. Published
`0.13.0rc2` does not include `Domain` yet; install the checkout to try it:

```sh
uv sync --locked --extra binary
```

## Declare tasks without DSN

```python
# app/billing/tasks.py
from iddqueue import Domain

billing = Domain("billing")

@billing.actor(store_results=True)
def charge(amount):
    return amount
```

`charge` is a standard Dramatiq Actor: queue `billing`, name `billing.charge`.
Other actors decorated by this domain use the same queue. An explicit
`actor_name="refund"` becomes `billing.refund`; broker and queue overrides are
rejected. Names are explicit, never inferred from directory names.

Importing the domain needs no default broker, DSN or PostgreSQL connection.
Direct calls and `.message()` work before registration; `.send()` raises a clear
error until startup. Keep middleware options on declarations: they are validated
against the actual broker during registration.

## One entry point

```python
# app/worker.py
import os
import dramatiq
from iddqueue import PostgresBroker
from app.billing.tasks import billing
from app.notifications.tasks import notifications

broker = PostgresBroker(url=os.environ["DATABASE_URL"])
dramatiq.set_broker(broker)
billing.register(broker)
notifications.register(broker)
```

DSN can instead come from your application settings loader at startup. Callers
can import actors before this bootstrap, then send after it. Each producer
process also runs its bootstrap once; configuration is not propagated across
Python processes. Workers and producers use the same domain/name declarations.
`set_broker` selects this broker for the standard CLI and composition defaults;
Domain registration explicitly binds the existing Actors.

Register before starting worker threads. Repeating registration on the same
broker is a no-op; a different broker or adding actors after registration raises
an error. For isolated tests/application instances create fresh Domain instances.
There is no hot rebinding or automatic discovery. The caller owns broker/pool
shutdown. Options/name collisions are preflighted; if a registration middleware
hook fails, actor handles reject sending again; abandon that Domain/broker
instead of retrying partial registration.

Native `.send_with_options()`, delay/timedelta, callbacks, messages,
pipelines/groups and Results remain Dramatiq APIs. Build/run compositions with
an explicitly configured broker; composing before startup must not implicitly
resolve a default broker. Async actors still require Dramatiq `AsyncIO` middleware
on the actual broker. Registration does not add middleware automatically.

## Runnable example and workers

[Billing](https://github.com/wa-pis/iddqueue/blob/main/examples/domains/billing.py)
and [notifications](https://github.com/wa-pis/iddqueue/blob/main/examples/domains/notifications.py)
are separate modules; [worker](https://github.com/wa-pis/iddqueue/blob/main/examples/domains/worker.py)
is the single entry point. It reads `DATABASE_URL`, falling back to libpq `PG*`
settings when unset. Initialize storage once with the same DSN:

```sh
export DATABASE_URL='postgresql://USER:PASSWORD@HOST/DATABASE'
uv run --no-sync iddqueue --dsn "$DATABASE_URL" init
uv run --no-sync dramatiq examples.domains.worker --use-spawn --processes 2 --threads 4
```

For separate groups, use that same entry point and select queues:

```sh
uv run --no-sync dramatiq examples.domains.worker --use-spawn --processes 2 --threads 4 --queues billing
uv run --no-sync dramatiq examples.domains.worker --use-spawn --processes 1 --threads 4 --queues notifications
```

Put `--queues` at the end because it accepts multiple queue names. Several
replicas may consume one domain. Each spawned process creates its own broker
and pool (default maximum 16 connections per pool); account for all processes,
consumers' reserved sessions and producer processes against PostgreSQL limits.
Shutdown uses the standard Dramatiq lifecycle.

A producer can import `add` freely and initialize once at its entry point:

```python
from examples.domains.billing import add
from examples.domains.worker import broker  # process bootstrap

try:
    message = add.send(2, 3)
    print(message.get_result(backend=broker.backend, block=True, timeout=15000))
finally:
    broker.close()
```

## Docker application example

Build the checkout's [Dockerfile](https://github.com/wa-pis/iddqueue/blob/main/examples/domains/Dockerfile):

```sh
docker build -f examples/domains/Dockerfile -t iddqueue-domains .
docker run --rm --env DATABASE_URL iddqueue-domains
```

The image copies package/example sources, installs the local package with the
binary extra, and uses exec-form CMD for the standard CLI. Supply a DSN reachable
from the container; host `localhost` is not the database inside the container.
For a domain-specific container, override the command using the same image:

```sh
docker run --rm --env DATABASE_URL iddqueue-domains \
  dramatiq examples.domains.worker --use-spawn --processes 2 --threads 4 --queues billing
```

Database credentials belong in runtime environment/settings or deployment
secrets, not the image. There is no new container runtime dependency or worker
process manager in IDDQueue. Container commands are examples; local verification
covers spawned CLI workers, and actual Docker execution depends on a running
engine.

Domains/queues separate code and workload, not database access. Use existing
schema/prefix namespaces for storage separation and database roles/databases
when access isolation is required. One standard worker uses one broker; several
DSNs require independent process bootstraps, not an automatic multi-broker worker.
