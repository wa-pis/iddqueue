# Evidence

2026-10-07: full suite 173 passed in 60.63s on Python 3.13.14, SQLAlchemy 2.1.3 and dedicated PostgreSQL 14.20 port 55433. Connection/Session commit/rollback and transactional NOTIFY, nested savepoint rollback, delay/dedup, invalid UUID SQL error and rollback recovery, inactive/logical/closed/Engine/multi-bind guards checked. Unsupported SQLite and AsyncSession rejected. Session flush/commit/rollback/close patched to fail during adapter call; publication succeeded without invoking them. Broker pool stays closed throughout transactional acceptance.

Initial test expected a literal non-default notification channel and duplicate UUID error, whereas existing broker uses hashed namespace channel and UPSERT; tests corrected to actual supported contract before final suite. SQLAlchemy 2.1 async test import requires greenlet, so dev-only SQLAlchemy asyncio extra added for rejection test; production sqlalchemy extra remains synchronous without that requirement.

Ruff/uv lock/docs/strict MkDocs/OpenSpec/build/LICENSE passed. Installed wheel base/monitoring/sqlalchemy profiles and isolated installed quickstart passed; core/base/monitoring work without SQLAlchemy. Development artifacts /tmp/iddqueue-sqlalchemy-build; published RC3 assets untouched. CI pending.

Signed implementation 1feb1df7e31054a767de98787d5b27aa8858afd3, signature verified, pushed main. Actual Tests 37541082307 итог success 6/6; Documentation 37541082310 success. Первая попытка Python 3.10/PG14: 172 passed, старый retry-wakeup test не получил NOTIFY за timeout 20ms, упал None.message_id; SQLAlchemy tests все прошли. Повтор failed job без изменения кода прошёл полный gate. Нестабильность старого timeout отмечена, production изменения для неё не выполнялись. Main spec synced; архив 2026-10-07.
