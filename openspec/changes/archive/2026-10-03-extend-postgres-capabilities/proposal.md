## Why

После завершения миграции и базовой совместимости нужны средства управления
очередями и оставшиеся проверки стандартных middleware. Пользователь попросил
записать обсуждённые возможности как последовательные шаги OpenSpec.

## What Changes

- Дедупликация отправки по пользовательскому ключу в области schema/prefix.
- Пауза и возобновление очереди с сохранением принятых сообщений.
- Отмена queued/delayed задач и добровольная проверка отмены выполняющимся actor.
- Проверки AgeLimit, TimeLimit, ShutdownNotifications, Callbacks, CurrentMessage.
- История попыток с ограниченным хранением и CLI диагностики.
- Атомарная пакетная отправка в обычной и внешней транзакции.
- PostgreSQL scheduler фиксированных интервалов с защитой от двойной отправки.
- Каждый этап проходит собственные проверки и фиксируется отдельным коммитом.

При создании change все пункты были планом новой работы. Теперь этапы 1–7
реализованы и проверены; актуальные статусы и результаты записаны в tasks/evidence.
GitHub setup и предыдущие шесть фич завершены и остаются в архиве.

## Capabilities

### New Capabilities

- `postgres-task-deduplication`: ключ отправки, конкурентная публикация и rollback.
- `postgres-queue-control`: pause/resume, включая delayed queue и prefetched задачи.
- `postgres-task-cancellation`: отмена до выполнения и cooperative cancellation.
- `postgres-attempt-history`: записи попыток, retention и чтение через CLI.
- `postgres-batch-publishing`: пакетная отправка с общим commit/rollback.
- `postgres-periodic-scheduling`: фиксированные интервалы и конкурентные schedulers.

### Modified Capabilities

- `dramatiq-composition-and-middleware`: проверки остальных стандартных middleware.

## Impact

Затрагиваются broker, SQL init/migrations, CLI, новые opt-in middleware,
документация и functional tests. Существующий синхронный Psycopg 3 runtime,
session locks, LISTEN/NOTIFY, лицензия и at-least-once сохраняются.
Новые таблицы требуют явной миграции; ORM и собственный workflow engine не нужны.
PyPI publication и изменение GitHub visibility не входят в scope.
