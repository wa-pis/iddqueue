## Context

Текущий stats показывает только число сообщений по состояниям. Для диагностики нагрузки нужны возраст ожидающих задач и наблюдаемость обработки в стандартном мониторинге Dramatiq. Текущая база — Psycopg 3 и Dramatiq 2.2.1; локальная миграция уже проверена. См. proposal.md и delta spec.

## Goals / Non-Goals

**Goals:** Метрики PostgreSQL-очереди, проверенная на реальном PostgreSQL.

**Non-Goals:** замена стандартного worker Dramatiq, exactly-once, автоматическая публикация релиза.

## Decisions

Стандартный Prometheus middleware подключается явно: Dramatiq 2 удалил его из default_middleware. Collector добавляет только показатели состояния PostgreSQL. CLI использует те же запросы. Возраст считать по отдельному времени постановки текущей попытки, если mtime не удовлетворяет этому контракту; измерение подтвердить тестом retries, а не трактовать время первоначального сообщения как точное ожидание. Соблюдать ограниченную cardinality: queue/state, без message_id/actor arguments. Количество retries и время обработки остаются стандартному middleware.

## Risks / Trade-offs

Агрегаты на большой очереди могут быть дорогими: индексы и интервал обновления проверяются на реалистичной выборке. Задержанные задачи нужно отличать от готового backlog, чтобы не выдавать плановую задержку за деградацию.

## Migration Plan

Выполнить tasks.md, повторить релевантные интеграционные проверки и сборку. Для изменения SQL подготовить явную миграцию существующей базы и обратимый путь до включения новой функции. Новые опциональные возможности включаются явно. После проверки синхронизировать delta spec и архивировать change.

## Implementation Notes

mtime подходит для ready-age только в queued. ENQUEUE при конфликте,
REQUEUE и CLI recover теперь обновляют mtime: текущая попытка не наследует
старый возраст. Ready_at = max(mtime, ETA), ready учитывает queued с наступившим
ready_at, scheduled — будущий ETA в queued/consumed. Consumed может означать
prefetch, поэтому это не счётчик выполняющихся actors. Delayed queues остаются
отдельными. Изменение схемы не требуется; исторические queued используют свой mtime.

stats без флагов сохраняет прежние общие totals; --json и --queue используют
queue_statistics. Collector выполняет тот же запрос с labels queue/state и
лениво импортирует prometheus_client. Extra monitoring переиспользует
Dramatiq[prometheus]; основной wheel не требует Prometheus.

Стандартный middleware импортируется из dramatiq.middleware.prometheus;
в example.py включается явно через EXAMPLE_PROMETHEUS. SQL collector размещается
в отдельном exporter-процессе; не внедряется в стандартный multiprocess endpoint.
Существующий индекс не изменён: измерения не показали необходимости нового.
