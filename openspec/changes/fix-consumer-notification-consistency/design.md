## Context

broker.__next__ выбирает full payload по наличию substring kwargs; CONSUME_ONE
обновляет строку только по ID/state без queue filter и без RETURNING payload.
fetch_by_id индексирует None при отсутствующей строке. purge_locks вызывается
лишь после опустошения notifications, в то время как успешный claim возвращает
управление раньше. Воспроизведения и приоритеты — review.md.

## Goals / Non-Goals

**Goals:** устранить четыре подтверждённых дефекта минимальным изменением
consumer/claim SQL, переиспользовать существующий unlock/wakeup путь.
**Non-Goals:** exactly-once, fencing всех actor side effects, новые payload
версии/protocols, переписывание broker, полный security аудит, cosmetic refactor.

## Decisions

1. Parse JSON hint один раз: scan sentinel либо message_id из legacy/full payload.
   PostgreSQL — источник actor payload; отказаться от эвристики substring kwargs.
   Сохранять wire compatibility, не заставлять producers менять формат.
2. Получать актуальный message вместе с успешным SQL UPDATE claim/RETURNING и
   проверять queue_name. Read-then-claim отдельными SELECT оставляет гонку;
   простая замена fetch_by_id недостаточна. Session lock рассчитывать в текущем
   namespace для ожидаемой очереди, не по obsolete полям notification.
3. Missing/terminal/moved row означает skip, не исключение/actor invocation;
   не держать advisory lock после неуспешного claim. Исторические внутренние
   helper signatures адаптировать только при необходимости и сверить callers.
4. Drain unlock_q перед prefetch guard и возвратом следующего claimed message.
   Нельзя unlock consumer connection из actor thread: Psycopg session owner
   остаётся consumer. Существующий NOTIFY_UNLOCKED сохранить для fast retries.

## Risks / Trade-offs

- Durable payload read может добавлять SQL → RETURNING текущего claim избегает
  отдельного round trip; full wire payload сохраняется для совместимости.
- SQL planner может получить advisory lock до отказа по predicates → сохранить
  release для неуспешного claim и проверить competing session acquisition.
- Изменение unlock timing влияет на retry race → regression с backlog,
  prefetch saturation и предыдущим fast retry сценарием.
- At-least-once допускает повторы при disconnect → не обещать fencing/effect
  isolation сверх выбранного контракта актуального payload на момент claim.

## Migration Plan

Новая storage migration не нужна. Добавить regressions на выделенной PostgreSQL,
исправить consumer, выполнить полный suite и обязательные checks, отдельный
commit/push и CI. Только после подтверждённого CI sync/archive.
