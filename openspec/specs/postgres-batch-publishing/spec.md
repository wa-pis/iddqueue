# postgres-batch-publishing Specification

## Purpose

Атомарно публиковать несколько сообщений с уменьшением числа обращений к PostgreSQL и поддержкой внешней транзакции.

## Requirements

### Requirement: Atomic batch

Batch API SHALL сохранять порядок возвращаемых сообщений, стандартные middleware enqueue hooks и delay metadata; ошибка SHALL откатывать весь пакет. Внешняя транзакция SHALL принадлежать вызывающему приложению.

#### Scenario: Batch commit
- **WHEN** пакет успешно зафиксирован
- **THEN** все задачи сохранены и уведомления доставляются после commit

#### Scenario: Batch rollback
- **WHEN** одна задача пакета не проходит валидацию либо внешняя транзакция откатывается
- **THEN** ни одна задача пакета и её deduplication keys не сохраняются

#### Scenario: Empty batch
- **WHEN** передан пустой пакет
- **THEN** возвращается пустой список без записи в БД

#### Scenario: Mixed queues and delay
- **WHEN** пакет содержит разные очереди и задержки
- **THEN** каждое сообщение сохраняет свои queue/ETA и корректные notifications

### Requirement: Async transactional batch

Система SHALL предоставлять awaitable batch на активной caller-owned Psycopg 3 AsyncConnection с сохранением порядка результатов, delay, дедупликации и соответствующих enqueue hooks. Лимит SHALL составлять 1000 входных сообщений; options SHALL соответствовать каждому входу. Внутренний savepoint SHALL защищать атомарность всего batch без commit/close/retry внешней транзакции.

#### Scenario: Commit mixed batch
- **WHEN** caller публикует пакет разных очередей, delay и deduplication options, затем выполняет commit
- **THEN** результаты возвращены в порядке входа, опубликованные задачи имеют корректные queue/ETA и уведомления; duplicates возвращают исходные Messages без повторной публикации

#### Scenario: Failure after first write
- **WHEN** SQL или валидация одного элемента завершается ошибкой после записи предыдущего
- **THEN** весь пакет и его новые deduplication записи откатываются до savepoint, NOTIFY пакета не доставляется; предыдущие бизнес-данные caller сохраняются до его решения о commit/rollback

#### Scenario: Cancelled batch
- **WHEN** coroutine отменена после первой записи внутри batch
- **THEN** отмена передаётся caller и savepoint отменяет весь batch без закрытия соединения и commit внешней транзакции

#### Scenario: Empty and invalid batch
- **WHEN** на активном async соединении передан пустой пакет
- **THEN** возвращается пустой список без SQL публикации

#### Scenario: Bounds and input mismatch
- **WHEN** передано больше 1000 сообщений, неподдерживаемые options или число options не равно числу сообщений
- **THEN** выдаётся ошибка без сохранения задач пакета
