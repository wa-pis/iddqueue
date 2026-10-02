============
 User Guide
============

Enabling Postgres Broker
========================

Dramatiq-pg is available on PyPI. Install it with pip::

    pip install dramatiq-pg

This package installs a Python package named ``dramatiq_pg`` and a script named
``dramatiq-pg``. To use Postgres as a Dramatiq message broker, use
``dramatiq_pg.PostgresBroker`` class.

::

   from dramatiq import set_broker
   from dramatiq_pg import PostgresBroker

   set_broker(PostgresBroker())

By default, ``PostgresBroker`` reads ``PG*`` environment variables. Further
options are detailed below.


Setting up PostgreSQL
=====================

Postgres is not a native broker. Dramatiq-pg stores messages in a single table
in its own schema. Thus you need to initialize schema and table before using
Postgres as a broker. For now, Dramatiq-pg does not manage the schema for you
and let's you use your database migration tool. Dramatiq-pg ships a
``schema.sql`` file as a starting point for initializing the database for
Dramatiq-pg.

::

    psql -f dramatiq_pg/schema.sql

Table and type are contained in a ``dramatiq`` schema.


Connection Configuration
========================

The ``PostgresBroker`` class accepts either a ``pool`` or an ``url`` argument.
The ``pool`` is a psycopg connection pool object.

::

   from dramatiq_pg import PostgresBroker
   from psycopg_pool import ConnectionPool

   pool = ConnectionPool("", min_size=0, max_size=8,
                         kwargs={"autocommit": True}, open=False)
   broker = PostgresBroker(pool=pool)


The ``url`` argument is a psycopg-compatible `connection string
<https://www.psycopg.org/psycopg3/docs/api/connections.html>`_, also called
*dsn*. Internally, ``PostgresBroker`` creates a ``ConnectionPool``. You
can customize de size of the pool by setting ``minconn`` and ``maxconn`` query
parameters. ``PostgresBroker`` reads ``minconn`` and ``maxconn`` only from URL,
not from keyword/value connection string.

::

   from dramatiq_pg import PostgresBroker

   broker = PostgresBroker(url="postgresql://user:password@host/dbname?minconn=8&maxconn=8")

``maxconn`` defaults to 16 and ``minconn`` defaults to 0. The pool opens
on first use, so constructing the broker doesn't connect to PostgreSQL or
start background threads. Create pools separately in each worker process;
do not share an opened pool across a process fork. Call ``broker.close()``
to close a pool created by the broker. For a supplied pool, its owner must
close it.


Result Storage
==============

Dramatiq-pg implements a `Result backend
<https://dramatiq.io/cookbook.html#results>`_ storing results in Postgres.
``PostgresBroker`` **enables automatically Results middleware** with a
``PostgresBackend`` sharing the same connection pool. Note that only actors
defined with ``store_results=True`` triggers result storage.

When using multiple brokers, you must pass the backend to
``message.get_result()`` method. This is a limitation of Dramatiq.
``PostgresBroker`` keeps a reference of it's auto-created backend.

::

   message = actor.send()
   message.get_result(backend=broker.backend)


Disabling Result Storage
------------------------

You can disable the ``Results`` middleware by passing ``results=False`` to
broker constructor.

::

   broker = PostgresBroker(url=conninfo, results=False)


Using Result Storage Alone
--------------------------

You may want to use Postgres as a result storage while using another message
broker (like RabbitMQ). To do this, directly use the ``PostgresBackend`` class.

::

   from dramatiq import Results
   from dramatiq_pg import PostgresBackend

   backend = PostgresBackend(url=conninfo)
   broker.add_middleware(Results(backend=backend))
