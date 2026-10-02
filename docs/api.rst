===============
 API Reference
===============

Dramatiq-pg ships a relatively simple API. Once you have initiated the broker,
you're almost done with Dramatiq-pg and can use Dramatiq as usual.


``dramatiq_pg.PostgresBroker(url="", pool=None, results=True)``
===============================================================

:pool:

   A psycopg pool object. Should be ConnectionPool for thread safety.

:url:

   A PostgreSQL connection string as understood by libpq. Dramatiq-pg extends
   libpq URL-style connection string with ``minconn`` and ``maxconn``
   parameters. Defaults to empty string, leading libpq to read values from
   environment variables.

:results:

   a boolean indicating whether to initialize a result backend. Default is True.

Defining both pool and url raises a ValueError.

**Attributes**

:backend:

   The PostgresBackend sharing the connection pool of the broker. Required to
   fetch result.


**Example**

Initialization:

.. code:: python

   from dramatiq_pg import PostgresBroker

   broker = PostgresBroker("postgresql://user:pass@host/dbname?maxconn=12")
   set_broker(broker)


Result usage:

.. code:: python

   message.get_result(backend=broker.backend)


``dramatiq_pg.PostgresBackend(url="", pool=None)``
==================================================

Postgres-backed implementation of result storage for Dramatiq.

pool and url arguments have the same meaning and the same behaviour as for
PostgresBroker.
