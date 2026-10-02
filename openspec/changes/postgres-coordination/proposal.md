## Why

Dramatiq имеет стандартные лимитеры и GroupCallbacks, но наш пакет не предоставляет для них PostgreSQL backend. Общий backend позволит использовать эти функции без Redis.

## What Changes

- Добавить PostgreSQL RateLimiterBackend: add, incr, decr, incr_and_sum, wait и wait_notify.
- Поддержать ConcurrentRateLimiter, BucketRateLimiter, WindowRateLimiter и Barrier.
- Добавить интеграцию стандартного GroupCallbacks с параметром barrier_ttl.

## Capabilities

### New Capabilities

- `postgres-rate-limits-and-barriers`: Лимиты и завершение групп через PostgreSQL.

### Modified Capabilities

Нет: новые контракты оформляются отдельно от незавершённой базовой миграции.

## Impact

Новый backend, отдельная координационная таблица и миграция SQL; примеры, тесты, экспорты пакета. Зависимость Redis не добавляется.

Статус: запланировано; реализация ожидается.
