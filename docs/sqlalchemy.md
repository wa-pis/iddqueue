# SQLAlchemy transactional publication (0.13.0)

This optional adapter is included in 0.13.0. Install it with
`uv pip install "iddqueue[binary,sqlalchemy]==0.13.0"`. SQLAlchemy remains optional for
producers; the broker and workers still use synchronous Psycopg 3.

```python
from sqlalchemy import create_engine, text
from iddqueue.sqlalchemy import enqueue_sqlalchemy
from app.billing.tasks import charge
from app.worker import broker  # register domains once at producer startup

engine = create_engine("postgresql+psycopg://USER:PASSWORD@HOST/DATABASE")
with engine.begin() as connection:
    connection.execute(text("UPDATE orders SET paid=true WHERE id=:id"), {"id": 42})
    enqueue_sqlalchemy(broker, charge.message(42), connection=connection)
# Business change and task commit together; rollback cancels both and NOTIFY.
```

Use a synchronous SQLAlchemy 2.x `Connection` or a `Session` with an explicit
bind. In a Session transaction, execute SQL or explicitly flush your business
changes before calling the helper. A logical `begin()` alone may not start the
underlying database transaction. The adapter does not autoflush or start a
separate database transaction. It never sends through the broker pool.

```python
from sqlalchemy.orm import Session

with Session(engine) as session:
    with session.begin():
        session.execute(text("UPDATE orders SET paid=true WHERE id=:id"), {"id": 42})
        enqueue_sqlalchemy(broker, charge.message(42), connection=session,
                           deduplication_key="order:42", deduplication_ttl=60000)
```

`delay`, `deduplication_key` and millisecond `deduplication_ttl` reuse
`PostgresBroker.enqueue_in_transaction` semantics. Middleware hooks describe
publication SQL, not eventual commit. Commit/rollback/close/retry belong to the
caller. SQL errors propagate as Psycopg errors; handle rollback or a SQLAlchemy
savepoint before reusing the transaction. Savepoint rollback cancels publication
inside that savepoint. This does not provide exactly-once processing.

Use the same database/schema/prefix as the worker. For a multi-bind Session,
pass the intended active Connection explicitly; a default bind is not evidence
that all business writes share its transaction. Engine, closed/inactive inputs,
other dialects/drivers and async inputs are rejected, without fallback enqueue.
An invalidated connection cannot silently reconnect for publication.

`AsyncSession`, `AsyncConnection`, asyncpg and psycopg2 are not supported by this
adapter. Do not pass a raw async driver into the synchronous broker or assume
`run_sync` makes arbitrary blocking Psycopg calls asynchronous. Use a separate
integration design if your business transaction is async.

No new storage schema is needed. [External schema management](migration.md#manage-schema-through-application-migrations)
remains independent of the ORM used by your application.
