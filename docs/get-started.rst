=============
 Get Started
=============

- Install dramatiq-pg package from PyPI::

     $ pip install "dramatiq-pg[binary]"

- Apply dramatiq\_pg/schema.sql file in your database::

     $ psql -f dramatiq_pg/schema.sql

- Before importing actors, define global broker with a connection
  pool::

      import dramatiq
      from dramatiq_pg import PostgresBroker

      dramatiq.set_broker(PostgresBroker(url="postgresql:///?maxconn=10"))

      @dramatiq.actor
      def myactor():
          ...

Now declare/import actors and manage worker just like any `dramatiq setup
<https://dramatiq.io/guide.html>`_ . An `example script
<https://gitlab.com/dalibo/dramatiq-pg/blob/master/example.py>`_ is available,
tested on CI.

The CLI tool ``dramatiq-pg`` allows you to flush queues, requeue messages, purge
old messages and show stats on the queue. See ``--help`` for details.

See more
in `full documentation
<https://gitlab.com/dalibo/dramatiq-pg/blob/master/docs/index.rst>`_.
