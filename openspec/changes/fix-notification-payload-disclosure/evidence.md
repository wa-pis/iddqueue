# Проверки security fix

## Regression

tests/func/test_notification_privacy.py: 12 комбинаций enqueue/ACK/NACK,
small/large payload и default/custom schema+prefix. Случайная NOLOGIN роль,
CONNECT grant, отдельная SET ROLE listener session; SELECT queue реально
вызывает InsufficientPrivilege. Cleanup закрывает consumer/pool/listener,
удаляет только fixture rows/schema и роль.

До fix: 6 failed, 6 passed; все small-message комбинации раскрывают actor,
kwargs/options вместо ID-only JSON. Large-message control уже безопасен.
После fix: notification privacy + consumer consistency: 22 passed in 0.39s.
Legacy full hint/authoritative SQL claim сохранены существующим regression.

## Trace

Три CASE в ENQUEUE/ACK/NACK заменены ID-only jsonb_build_object.
Transactional/batch/dedup публикация идут через _write_enqueue/ENQUEUE;
scheduler публикует через enqueue_in_transaction. CLI retry/unlock уже ID-only;
results отправляет UUID, cancellation ID, control queue name, coordination
empty payload. Task arguments/options отсутствуют во всех этих sinks.
Схема и параметры запросов не изменены; сторонний LISTEN full-JSON клиент
обязан получать SQL payload по ID. UUID/activity metadata не защищены channels.

## Checks

- Ruff iddqueue tests/unit tests/func example.py: passed.
- scripts/check_docs.py: passed.
- poetry check: passed.
- strict OpenSpec: 19/19 passed.
- Полный functional/unit набор: 143 passed in 43.75s.
- Независимое read-only Codex Security patch review: no bypass/regression findings. Все pg_notify и общие publication paths прослежены.
- GitHub CI: pending. Публикация не выполнялась.

Явные USAGE/SELECT assertions: 12 passed in 0.17s; restricted table lookup
для has_table_privilege требует schema USAGE, поэтому проверка SELECT grant
выполняется admin session для той же роли; реальный SELECT denied проверяется
restricted listener. Предыдущая introspection попытка дала 12 setup failures,
не воспроизведение disclosure.
