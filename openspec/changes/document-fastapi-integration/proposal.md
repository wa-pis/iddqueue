## Why

Пользователю нужен понятный и проверенный способ применять IDDQueue в FastAPI. Синхронный PostgreSQL broker уже подходит для отправки задач, но прямой вызов `.send()` из async endpoint блокирует event loop; жизненный цикл pool также требует явного владельца.

## What Changes

- Добавить небольшой запускаемый FastAPI-пример: broker в lifespan, async endpoint с `await asyncio.to_thread(actor.send, ...)`, ответ с message_id после успешной отправки.
- Показать отдельный запуск Dramatiq worker и вариант обычного `def` endpoint.
- Документировать закрытие ресурсов, at-least-once и ограничение: существующий transactional enqueue не принимает Psycopg AsyncConnection.
- Проверить пример на выделенном PostgreSQL, жизненный цикл и отсутствие блокировки event loop; подключить проверки к существующему CI.

## Capabilities

### New Capabilities

Нет: пример использует существующий публичный API.

### Modified Capabilities

Нет: runtime-контракты не меняются. Для документации и проверяемого примера установлено `skip_specs: true`.

## Impact

Пример, документация, acceptance tests, при необходимости uv dependency group для примера и CI/release gate. FastAPI не становится runtime-зависимостью IDDQueue. Async broker, async producer, ORM и новая схема PostgreSQL в этот change не входят.
