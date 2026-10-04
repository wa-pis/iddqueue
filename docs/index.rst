========
IDDQueue
========

IDDQueue provides a synchronous PostgreSQL broker and Results backend for
`Dramatiq <https://dramatiq.io/>`_. It uses Psycopg 3, JSONB, LISTEN/NOTIFY and
session advisory locks, without an ORM or a separate broker service.
Delivery is at least once: actors and callbacks must be idempotent.

One queue table stores messages and results; coordination, deduplication,
queue control, attempts and schedules use separate tables. Notifications wake
workers, which claim authoritative rows; startup and idle recovery also scan
storage. Fixed interval scheduling polls due rows.

Contents
========

- `Get Started <get-started.rst>`_
- `User Guide <user-guide.rst>`_
- `API Reference <api.rst>`_
- `Deployment Guide <deployment-guide.rst>`_
- `Compatibility and support <../SUPPORT.md>`_
- `Contributing <../CONTRIBUTING.md>`_
- `Release checks <release.md>`_
- `IDDQueue changelog <../CHANGELOG.md>`_
- `Historical upstream changelog <changelog.rst>`_
- `Why PostgreSQL <why.rst>`_

`Source <https://github.com/wa-pis/iddqueue>`_ and
`issues <https://github.com/wa-pis/iddqueue/issues>`_ require repository access.
PyPI publication is pending. This fork preserves DALIBO's PostgreSQL
`LICENSE <../LICENSE>`_ and upstream credits in `README <../README.md>`_.
