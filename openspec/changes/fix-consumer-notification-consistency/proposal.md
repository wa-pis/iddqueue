## Why

Критическое ревью выявило четыре воспроизводимых дефекта consumer: устаревший
payload, claim чужой normal/DQ очереди, падение при удалённой строке и задержку
освобождения session locks под backlog. Нужны исправления до дальнейшего
расширения возможностей; последний успешный suite не покрывает эти сценарии.

## What Changes

- Читать актуальный payload PostgreSQL вместе с успешным claim, а NOTIFY
  использовать как подсказку ID, сохраняя поддержку прежнего wire payload.
- Ограничить claim очередью consumer и состоянием, не выполнять obsolete hints.
- Пропускать уведомления отсутствующих/terminal/moved messages без падения.
- Освобождать накопленные ACK/NACK locks до следующего claim/prefetch ожидания,
  сохраняя retry wakeup после unlock.
- Добавить детерминированные regression tests и evidence исправлений.

## Capabilities

### New Capabilities

- `postgres-consumer-consistency`: актуальный queue claim, stale notifications
  и своевременное освобождение session locks.

### Modified Capabilities

Нет. At-least-once и существующие namespace/pause/cancellation контракты сохраняются.

## Impact

iddqueue/broker.py, functional/unit regression tests, docs и OpenSpec evidence.
Нет новых dependencies, фоновых сервисов, ORM, SQL tables или security gates.
NOTIFY channels/форматы остаются совместимыми. Ponytail: упростить разбор hint
и переиспользовать SQL claim вместо добавления отдельного orchestration слоя.
