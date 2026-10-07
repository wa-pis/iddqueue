## 1. Async publication

- [x] 1.1 Добавить enqueue_in_transaction_async с проверкой AsyncConnection/INTRANS, общей подготовкой/SQL и caller-owned lifecycle без retries.
- [x] 1.2 Поддержать delay и дедупликацию под async savepoint; переиспользовать минимальные SQL/validation helpers, сохранить sync поведение и hooks.
- [x] 1.3 Добавить enqueue_many_in_transaction_async: порядок, лимит 1000, aligned options, mixed delay/dedup и атомарный savepoint.

## 2. Acceptance tests

- [x] 2.1 На выделенном PostgreSQL проверить бизнес-запись + задача + NOTIFY до/после commit и после rollback, соединение остаётся caller-owned.
- [x] 2.2 Проверить delay/ETA, duplicate identity, разные queues/schema/prefix, hooks и откат nested savepoint; сравнить с sync сценариями.
- [x] 2.3 Проверить idle/ошибочный тип, пустой batch, лимиты/options, SQL ошибку после первой записи и сохранение предшествующих бизнес-данных после rollback savepoint.
- [x] 2.4 Детерминированно отменить заблокированный одиночный SQL и batch после первой записи; проверить propagation, отсутствие частичных task/key/NOTIFY и reuse соединения после rollback, без случайных sleep.
- [x] 2.5 Проверить, что ожидающий PostgreSQL async I/O не блокирует другую coroutine; не обещать async пользовательские middleware hooks.

## 3. Documentation and validation

- [x] 3.1 Добавить framework-independent runnable async transaction recipe; обновить API/FastAPI/user-guide/актуальные ограничения, явно сохранить отсутствие этой возможности в RC4 и async SQLAlchemy adapter.
- [x] 3.2 Выполнить полный tests/unit tests/func на выделенном PostgreSQL, Ruff, uv lock --check, strict docs и openspec validate --all --strict; записать реальные команды/результаты в evidence.md. Build/LICENSE — при packaging изменениях.
- [x] 3.3 Сделать отдельный подписанный feature commit, push в wa-pis/iddqueue main и проверить фактический GitHub CI; не публиковать пакет/tag.
- [x] 3.4 После успешной проверки синхронизировать delta specs, архивировать change и обновить roadmap/evidence по фактическим результатам.
