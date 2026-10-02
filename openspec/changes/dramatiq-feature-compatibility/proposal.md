## Why

Pipelines, groups, async actors и on_retry_exhausted реализованы в Dramatiq, но не подтверждены нашим набором интеграционных тестов. Нужны проверенные сценарии использования PostgreSQL broker.

## What Changes

- Подтвердить pipelines и обычные groups с PostgreSQL Results.
- Подтвердить async actors со стандартным AsyncIO middleware.
- Подтвердить on_retry_exhausted и поддержку delay как timedelta через Actor API.
- Документировать стандартные actor priorities как приоритет worker-prefetch, не обещая глобальный порядок PostgreSQL-очереди.

## Capabilities

### New Capabilities

- `dramatiq-composition-and-middleware`: Совместимость со стандартными возможностями Dramatiq.

### Modified Capabilities

Нет: новые контракты оформляются отдельно от незавершённой базовой миграции.

## Impact

Интеграционные тесты, примеры и документация; минимальные исправления брокера только при обнаруженной несовместимости. Group completion callbacks зависят от postgres-coordination.

Статус: запланировано; реализация ожидается.
