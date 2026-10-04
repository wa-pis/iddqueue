===========
Get Started
===========

Install a locally built artifact (publication is pending)::

    uv build
    pip install "dist/iddqueue-0.13.0-py3-none-any.whl[binary]"

The binary extra supplies libpq through Psycopg's binary distribution. Base
installation instead needs system libpq. Configure PGHOST, PGPORT, PGUSER,
PGPASSWORD and PGDATABASE, or pass a connection string to PostgresBroker.

Initialize fresh storage, or upgrade existing storage with workers stopped::

    iddqueue init
    iddqueue upgrade

Choose one command for the appropriate starting state. Both include the
optional tables and cancellation columns; raw schema.sql alone is incomplete.
Global flags select the same storage area for every command::

    iddqueue --schemaname myapp --prefix jobs_ init

Before importing actors, configure the broker in your application::

    import dramatiq
    from iddqueue import PostgresBroker

    broker = PostgresBroker()
    dramatiq.set_broker(broker)

    @dramatiq.actor(store_results=True)
    def add(left, right):
        return left + right

For an application module named tasks, run ``dramatiq tasks`` separately, then
send ``message = add.send(2, 3)`` from a producer that imports tasks. Retrieve
``message.get_result(backend=broker.backend, block=True, timeout=10000)``.
Timeouts are milliseconds. A worker must register the actor before consuming.

Executable acceptance example
=============================

`quickstart.py <quickstart.py>`_ runs the same enqueue/result flow using an
in-process worker in an isolated random schema. Use a dedicated PostgreSQL
instance; it creates and drops only that schema. The release check executes
this exact file from a clean installed wheel environment outside checkout::

    export IDDQUEUE_TEST_DATABASE=dedicated
    python docs/quickstart.py
    uv run --locked --extra binary --extra monitoring python scripts/check_package.py --quickstart dist/iddqueue-0.13.0-py3-none-any.whl

It asserts six storage tables, the enqueued row and result 5, then stops the
worker, closes pools and drops the schema. Runtime examples and operations:
`User Guide <user-guide.rst>`_ and `Deployment Guide <deployment-guide.rst>`_.
