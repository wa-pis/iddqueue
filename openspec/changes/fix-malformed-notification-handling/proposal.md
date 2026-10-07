## Why

Security review commit 28044df выявил падение consumer на некорректном PostgreSQL NOTIFY. Отправитель с CONNECT/pg_notify, без доступа к queue, может вызвать перезапуск и освобождение processing locks.

## What Changes

- Пропускать malformed JSON, не-object payload, отсутствующий/некорректный UUID без закрытия consumer sessions.
- Сохранить ID-only, legacy full hints и настоящий scan marker; задача всегда берётся из durable claim.
- Добавить регрессию с ролью без queue privileges и удерживаемым processing lock.

## Capabilities

### New Capabilities
Нет.

### Modified Capabilities
- `postgres-consumer-consistency`: tolerance для malformed notifications.

## Impact

iddqueue/broker.py и functional tests; без schema/dependency/API изменений. До RC4 выполнить проверки и отдельный signed commit/push/CI.
