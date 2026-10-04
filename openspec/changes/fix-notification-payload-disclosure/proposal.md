## Why

Codex Security scan c4bd206b-06e6-4a9b-9a72-4d0a1d8765f0 подтвердил CWE-200 / medium: ENQUEUE/ACK/NACK публикуют полные задачи <8000 bytes в PostgreSQL NOTIFY, доступный отдельной роли той же БД без SELECT очереди. Табличные permissions не защищают скопированные аргументы/options.

## What Changes

- Только message_id в исходящих task notifications независимо от размера; закрыть все три SQL sinks.
- Проверить фактическую границу PostgreSQL роли без schema USAGE/queue SELECT и все lifecycle paths.
- Сохранить приём legacy full hints и исполнение authoritative SQL payload.
- Обновить changelog/migration guidance: fix относится к новым producers/workers; старые продолжают раскрывать данные.

## Capabilities

### New Capabilities

Нет.

### Modified Capabilities

- `postgres-consumer-consistency`: ограничение исходящих notification payloads при сохранении совместимости входящих hints.

## Impact

iddqueue/broker.py, functional regressions, README/docs/migration.md/CHANGELOG.md и OpenSpec evidence. Схема, зависимости, каналы и публичный API не меняются. Произвольные downstream LISTEN consumers полного JSON должны читать разрешённую таблицу по ID. Dependabot Pygments и malformed-notification hardening вне scope; публикация запрещена без отдельного запроса.
