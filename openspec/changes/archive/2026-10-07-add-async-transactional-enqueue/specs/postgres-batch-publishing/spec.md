## ADDED Requirements

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
