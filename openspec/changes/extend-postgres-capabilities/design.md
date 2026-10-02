## Context

Очередь содержит queued/consumed/done/rejected, message JSONB, Results и TTL.
Broker использует UUID upsert, enqueue hooks, внешнюю транзакцию,
долгоживущие consumer sessions и session advisory locks. Coordination хранит
счётчики/события; она не является таблицей управления очередями.
Проверены 65 tests и шесть комбинаций GitHub CI. Новые пункты ещё не реализованы.

## Goals / Non-Goals

**Goals:** последовательные небольшие расширения, атомарные изменения PostgreSQL,
явные наблюдаемые контракты и отдельный commit на каждый завершённый этап.

**Non-Goals:** exactly-once execution, ORM, async broker, DAG engine,
принудительное безопасное убийство actor, cron/calendar/timezone scheduler
и автоматическая публикация пакета.

## Decisions

1. Дедупликация: отдельная таблица ключей с UNIQUE по логической очереди/ключу,
message_id и expires_at внутри schema/prefix. TTL обязателен; SQL clock служит
источником времени. Claim key и enqueue выполняются одной транзакцией.
Истечение допускает новую отправку; purge сообщения не сокращает TTL ключа.
Повтор возвращает исходный ID даже если соответствующая очередь уже очищена.
Hooks не должны повторно представлять дубль как фактически опубликованный message.
Dedup подавляет отправку; идемпотентность side effects остаётся обязанностью actor.

2. Pause: отдельная небольшая control table, normal и .DQ адресуются одной
логической очередью. SQL claim и opt-in middleware перед исполнением согласуют
проверку pause, включая prefetched задачи. В SQL control row сериализуются pause
и разрешение старта; момент разрешения старта считается границей started.
Не спать бесконечно в worker thread: задача возвращается в хранение без
расходования retry budget. Resume отправляет namespace-aware wakeup.

3. Cancellation переиспользует механизм разрешения старта pause. Нужны явный
cancelled status, CLI/API и отдельная ошибка Results cancellation; не кодировать
отмену как rejected actor failure. Уже started задача получает request flag,
который проверяет actor через CurrentMessage. Ack/retry/recover не должны
воскрешать cancelled сообщение. Обновить schema enum, metrics и CLI totals.

4. Middleware проверять штатными реализациями Dramatiq. TimeLimit test использует
CPU-bound actor на CPython; blocking syscall не обязан прерываться. Shutdown
проверяется управляемым процессом с cleanup, без произвольного sleep assertion.

5. Attempt history — opt-in middleware и отдельная таблица с уникальным
attempt_id; concurrent retries не идентифицировать только счётчиком retries.
Не записывать args/kwargs; текст ошибки ограничивать как существующий pg_failure.
Crash оставляет incomplete запись; не заявлять точное время смерти worker.
CLI поддерживает pagination; purge history отдельно от queue/results retention.

6. Batch следует обычному enqueue и enqueue_in_transaction, общие middleware
hooks сохраняются на каждое сообщение. Внешний вызов использует savepoint:
ошибка не оставляет частично записанный batch даже если caller ловит исключение.
Уведомления группировать только без потери message IDs/namespace.
Для больших пакетов ограничить размер явно и измерить query count/время;
COPY и новые dependencies не вводить без измеренной необходимости.

7. Scheduler — отдельная interval schedule table и один CLI foreground loop.
Для due rows SELECT FOR UPDATE SKIP LOCKED, отправка и продвижение next_run
в одной транзакции; deterministic occurrence key использует dedup API.
Время берётся из PostgreSQL; хранение UTC. Missed runs coalesce в одну задачу.
Cron expressions и catch-up всех пропусков не входят в первый этап.

8. Новые таблицы/enum обновляются явным idempotent CLI migration SQL в каждом
нужном этапе; чистый init и существующая база дают одинаковую схему.
Миграцию выполнять при остановленных workers; старые и новые control-aware
workers не смешивать. Для rollback сначала drain новые типы данных;
не обещать destructive автоматический downgrade.

## Risks / Trade-offs

- Pause/cancel требуют проверки prefetched задач, одной проверки SQL claim мало.
- Быстрые retries и lock release уже имели гонки; новые transitions проверить
детерминированными barriers и несколькими processes.
- Дедупликация хранит ключи до TTL и не гарантирует однократные side effects.
- История увеличивает write load; opt-in и retention обязательны.
- Scheduler доставляет at-least-once, даже если occurrence опубликован единожды.

## Migration Plan

Порядок: dedup → pause → cancellation → middleware coverage → history →
batch → scheduler. Pause зависит от control migration; cancellation от pause;
scheduler от dedup/transactional publishing. Остальные технически независимы,
но реализуются последовательно. Каждый этап включает code/tests/docs/spec evidence,
полный dedicated PostgreSQL suite, Ruff, poetry check, strict OpenSpec,
build при packaging/SQL resources изменениях и GitHub CI, отдельный commit/push.
Архивировать общий change после всех этапов; промежуточные completed tasks
и commits служат evidence, prepared CI не является выполненным тестом.

## Open Questions

Нет блокирующих вопросов для планирования. Fixed intervals вместо cron,
TTL dedup явно задаётся вызывающим приложением, history opt-in — границы
первой реализации. Новое пожелание, меняющее эти контракты, сначала отражать
в proposal/specs/design/tasks.

## Этап 2 — уточнение реализации

Queue control opt-in: PostgresBroker(queue_control=True), middleware gate первый,
до других before_process hooks. Deferred pause не запускает after_skip hooks,
поскольку стандартный Results иначе сохраняет None. Consumer ack возвращает
такую задачу в queued без изменения retries/ETA и освобождает session lock.
Общий control row с FOR SHARE сериализует claim/start gate с pause UPDATE.
Resume отправляет scan wakeup в normal/DQ; consumer читает durable pending rows.
Граница started — commit разрешающей SQL gate транзакции; уже разрешённый actor
может завершиться после pause. Все workers области должны включить queue_control.


## Этап 3 — уточнение cancellation

Queue row started/cancel_requested сериализуется FOR UPDATE со start gate.
Cancel до разрешения старта записывает cancelled и NOTIFY Results; started
получает request flag. Cooperative API cancellation_requested(id) — проверка
флага, actor сам выполняет cleanup и возвращается; его результат обычный done.
При retry request сохраняется, started сбрасывается; следующая gate записывает
cancelled. Все workers должны включать queue_control для prefetched protection.
Cancelled сохраняется до purge; ResultCancelled наследует ResultFailure.
Upgrade enum/columns выполняется при остановленных workers до нового runtime.


## Этап 4 — фактический контракт middleware

Стандартный Callbacks.on_failure вызывается на каждой неудачной попытке, а не
только при exhausted retries; проверяются обе попытки и success payload.
CurrentMessage проверяется на одной worker thread после failure и success.
TimeLimit запускается штатным process_boot и прерывает CPU-bound Python actor;
обычный Worker проверяет два attempts/Results/rejected/lock release.
ShutdownNotifications проверяется отдельным CLI процессом: started witness,
SIGTERM, cleanup witness, normal result/done и освобождение lock.
Runtime middleware не копируются и не переопределяются.


## Этап 5 — фактический контракт истории

PostgresBroker(attempt_history=True) добавляет lifecycle middleware последним:
before_process после штатных проверок, after_process перед Retry/Results hooks.
Отдельная таблица attempts не имеет FK на queue; UUID попытки находится только
на MessageProxy, не в payload/options. Начало и окончание берутся из SQL clock,
ошибка ограничена 2000 символами. Incomplete означает отсутствие окончания,
включая ещё выполняющийся actor; точное время crash не известно.
CLI history list MESSAGE_UUID использует keyset pagination по attempt_id UUID;
временной порядок определяется timestamps. Положительный maxage у history purge
удаляет по started_at, включая старые incomplete, независимо от queue/Results.
Это diagnostic middleware: обычные ошибки hooks логируются Dramatiq, при отказе
БД возможны пропуски; запись истории не является транзакцией side effects actor.


## Этап 6 — фактический контракт batch

enqueue_many(messages, options=None) и enqueue_many_in_transaction(...,
connection=...) принимают до 1000 сообщений и aligned dict options с delay,
deduplication_key, deduplication_ttl. Возвращают input order, включая исходные
messages для дублей. Empty не делает SQL; внешний вариант всё равно требует
active transaction. Внешний вызов оборачивает весь пакет в savepoint; ошибок
соединения автоматически не повторяет, caller сохраняет commit/rollback.
Plain batch использует Psycopg executemany/pipeline существующего ENQUEUE:
100 сообщений остаются 100 SQL enqueue statements, но один cursor вызов и
одна transaction вместо 100. Mixed/dedup batch переиспользует обычный claim
последовательно; performance улучшение для dedup не заявляется.
After hooks выполняются только после успешного пакета (после commit для owned
transaction); внешние hooks могут предшествовать последующему caller rollback.
Python side effects hooks не атомарны с БД, как и при одиночной отправке.
