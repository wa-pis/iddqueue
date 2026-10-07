## Why

Приложение с Psycopg AsyncConnection сейчас не может атомарно публиковать задачу вместе со своими бизнес-данными через IDDQueue. Отправка через отдельный pool не входит в его транзакцию, а перенос всей транзакции в поток требует изменения приложения.

## What Changes

- Добавить awaitable методы PostgresBroker.enqueue_in_transaction_async и enqueue_many_in_transaction_async для активной Psycopg 3 AsyncConnection.
- Сохранить caller-owned commit/rollback/close, delay, дедупликацию, порядок batch и enqueue hooks; не повторять внешнюю транзакцию автоматически.
- Проверить отмену coroutine, rollback savepoint и отсутствие преждевременной видимости задач/NOTIFY.
- Добавить framework-independent пример и обновить ограничения API/FastAPI документации.
- Синхронные broker/consumer/results и существующие методы сохраняются; async SQLAlchemy, asyncpg и async actor.send не входят в change.

## Capabilities

### New Capabilities

Нет.

### Modified Capabilities

- `transactional-task-publishing`: отдельный async вход с сохранением атомарности и владения транзакцией.
- `postgres-batch-publishing`: async batch в caller transaction с атомарным savepoint.

## Impact

iddqueue/broker.py и минимальные общие SQL/helpers для sync/async путей; functional/unit tests, docs/api.md, docs/recipes.md, docs/fastapi.md и актуальные описания ограничений. Новые зависимости и DDL не требуются. RC4 остаётся неизменным; публикация будущей версии — отдельный запрос.
