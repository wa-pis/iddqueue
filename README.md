![Dramatiq-pg](https://gitlab.com/dalibo/dramatiq-pg/raw/master/docs/logo-horizontal.png?inline=false)

[Dramatiq](https://dramatiq.io/) is a simple task queue implementation for
Python3. dramatiq-pg provides a Postgres-based implementation of a dramatiq
broker.


## Features

- Super simple deployment: Single table, no ORM.
- Stores message payload and results as native JSONb.
- Uses LISTEN/NOTIFY to keep worker sync. No polling.
- Implements delayed task.
- Reliable thanks to Postgres MVCC.
- Self-healing: automatic purge of old messages. Automatic recovery after
  crash.
- Utility CLI for maintainance: flush, purge, stats, etc.

Note that dramatiq assumes tasks are idempotent. This broker makes the same
assumptions for recovering after a crash.


## Installation

- Install dramatiq-pg package from PyPI:
  ``` console
  $ pip install "dramatiq-pg[binary]"
  ```
  Requires Python 3.10+, Dramatiq 2.2.1+ and Psycopg 3.3.6+.
- Init database schema with `init` command.
  ``` console
  $ dramatiq-pg init
  ```
  Or adapt `dramatiq-pg/schema.sql` to your needs.
- Before importing actors, define global broker with a connection
  pool:
  ``` python
  import dramatiq
  from dramatiq_pg import PostgresBroker

  dramatiq.set_broker(PostgresBroker(url="postgresql://localhost/postgres"))

  @dramatiq.actor
  def myactor():
      ...
  ```

Now declare/import actors and manage worker just like any [dramatiq
setup](https://dramatiq.io/guide.html). An [example
script](https://gitlab.com/dalibo/dramatiq-pg/blob/master/example.py) is
available, tested on CI.

The CLI tool `dramatiq-pg` allows you to requeue messages, purge old messages
and show stats on the queue. See `--help` for details.

[Dramatiq-pg
documentation](https://gitlab.com/dalibo/dramatiq-pg/blob/master/docs/index.rst)
is hosted on GitLab and give you more details on deployment and operation of
Postgres as a Dramatiq broker.


## Integration

**Django** : Use
[django-dramatiq-pg](https://github.com/uptick/django-dramatiq-pg/) by [Curtis
Maloney](https://gitlab.com/FunkyBob). It includes configuration, ORM model and
database migration.


## Support

If you encounter a bug or miss a feature, please [open an issue on
GitLab](https://gitlab.com/dalibo/dramatiq-pg/issues/new) with as much
information as possible.

dramatiq_pg is available under the PostgreSQL licence.


## Credit

Thanks to all contributors :

- Andy Freeland
- Curtis Maloney, Django support.
- Federico Caselli, bugfixes.
- Giuseppe Papallo, bugfixes.
- Rafal Kwasny, improvements.


The logo is a creation of [Damien CAZEILS](http://www.damiencazeils.com/)


## Development

```console
poetry install --extras binary
poetry run dramatiq-pg init
poetry run python tests/pypsql < tests/func/schema.sql
poetry run pytest tests/unit tests/func
```

Configure the test database with `PGHOST`, `PGPORT`, `PGUSER`, `PGPASSWORD`
and `PGDATABASE`. Tests terminate database connections and restart workers;
use a dedicated test database. `docker-compose.yml` provides PostgreSQL 18.

Version 0.13 uses Psycopg 3 pools; Psycopg 2 pools are no longer supported.
Broker-created pools open on first use and default to zero idle connections.
Call `broker.close()` on shutdown. If you supply a pool, close it yourself
and create it separately in each worker process.


## Transactional publishing

Use `enqueue_in_transaction` to publish a task atomically with application
changes in the same PostgreSQL database:

```python
import psycopg

with psycopg.connect(dsn) as connection:
    with connection.transaction():
        connection.execute("UPDATE orders SET status = %s WHERE id = %s",
                           ("confirmed", order_id))
        broker.enqueue_in_transaction(send_receipt.message(order_id),
                                      connection=connection)
```

The connection must already have an active transaction. The broker does not
commit, roll back, close, or retry that transaction. PostgreSQL makes the task
and its notification visible on commit; rollback cancels both. `delay` is in
milliseconds, measured from enqueue time. Enqueue middleware hooks run around
the SQL operation: `after_enqueue` does not mean the outer transaction has
committed. Workers still provide at-least-once delivery.

### PostgreSQL limiters and group callbacks

Existing installations must add the coordination table before enabling this
backend. Fresh `dramatiq-pg init` installations include it:

```python
import psycopg
from dramatiq_pg import generate_coordination_sql

with psycopg.connect("postgresql://localhost/app") as connection:
    connection.execute(generate_coordination_sql(schema="dramatiq", prefix=""))
```

The upgrade is idempotent and preserves queue data. To reverse it, first stop
users of the coordination backend, then drop only `dramatiq.coordination`
(adjust schema and prefix when customized).

```python
from dramatiq.middleware import GroupCallbacks
from dramatiq.rate_limits import ConcurrentRateLimiter
from dramatiq_pg import PostgresRateLimiterBackend

limits = PostgresRateLimiterBackend(pool=broker.pool)
broker.add_middleware(GroupCallbacks(limits, barrier_ttl=900_000))

with ConcurrentRateLimiter(limits, "external-api", limit=5).acquire():
    call_external_api()
```

The backend also supports `BucketRateLimiter`, `WindowRateLimiter` and `Barrier`.
Durations are milliseconds, except Dramatiq's sliding `window` in seconds.
Use unique UUID barrier keys. Events survive missed notifications until their
TTL expires. `wait` holds one pool connection; size the pool for simultaneous
waiters and publishers. Schedule `limits.purge()` periodically to remove
expired coordination rows. `close()` closes only a pool owned by the backend.

Choose a TTL longer than the longest operation: an expired concurrency slot
can be acquired while its original task is still running. Standard
`GroupCallbacks` counts successful deliveries; repeated deliveries can contribute
again and callbacks are not guaranteed exactly once. A group with failed tasks
may never reach its barrier, and expired group state cannot reconstruct progress.

### Standard Dramatiq composition and middleware

The broker supports the standard `dramatiq.pipeline` and `dramatiq.group` APIs.
Enable result storage on each actor whose result you want to retrieve:

```python
import dramatiq

@dramatiq.actor(store_results=True)
def multiply(value, factor=2):
    return value * factor

chain = dramatiq.pipeline([multiply.message(3), multiply.message(4)])
chain.run()
assert chain.get_result(block=True) == 24

batch = dramatiq.group([multiply.message(3), multiply.message(4)])
batch.run()
assert list(batch.get_results(block=True)) == [6, 8]
assert batch.completed_count == 2
```

Pipelines append a predecessor's result to the next actor's positional arguments.
A failed step does not enqueue its successor. `get_results` returns group results
in submission order; tasks may finish in another order. `completed_count` reads
stored results, so actors without result storage are not counted and expired
results no longer count. Terminal failures raise `ResultFailure`.

For coroutine actors, add Dramatiq's standard `AsyncIO` middleware before
declaring the actors, in the module loaded by every worker:

```python
import asyncio
from dramatiq.middleware import AsyncIO

broker.add_middleware(AsyncIO())

@dramatiq.actor(store_results=True)
async def async_task(value):
    await asyncio.sleep(0.01)
    return value
```

The PostgreSQL broker remains synchronous. Use async clients or
`asyncio.to_thread` for blocking I/O inside coroutine actors.

The default `Retries` middleware supports `on_retry_exhausted` (singular):

```python
@dramatiq.actor
def report_failure(message, retry_metadata):
    # message is a serialized Dramatiq message; metadata has
    # retries and max_retries. Make any external action idempotent.
    print(message["message_id"], retry_metadata)

@dramatiq.actor(max_retries=3, on_retry_exhausted="report_failure")
def unreliable_task():
    raise RuntimeError("unavailable")
```


`Actor.send_with_options(delay=timedelta(seconds=1))` accepts a `timedelta`;
Dramatiq converts it to milliseconds before calling the broker. Direct broker
methods use millisecond delays. A delay specifies the earliest execution time,
not an exact schedule.

Smaller actor `priority` numbers run first among messages already prefetched by
a worker. PostgreSQL does not provide global priority ordering across workers
or all queued messages. Ordinary groups need only Results; completion callbacks
additionally require `GroupCallbacks` and the PostgreSQL coordination table
shown above. Pipelines, retries and callbacks retain at-least-once delivery.
