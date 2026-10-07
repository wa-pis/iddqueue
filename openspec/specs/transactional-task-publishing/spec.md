# transactional-task-publishing Specification

## Purpose
Транзакционная отправка задач: определить проверяемый контракт этой возможности для PostgreSQL-проекта и совместимости с Dramatiq.

## Requirements

### Requirement: Atomic publication

Отправка через транзакцию приложения SHALL фиксироваться или откатываться вместе с её бизнес-данными.

#### Scenario: Commit

- **WHEN** приложение изменило запись и поставило задачу в одной транзакции, затем выполнило commit
- **THEN** сохранены и запись, и задача; потребитель может получить сообщение

#### Scenario: Rollback

- **WHEN** транзакция отменена после постановки задачи
- **THEN** ни бизнес-изменение, ни задача не сохранены; уведомление enqueue не доставлено

### Requirement: Caller owns transaction

Брокер SHALL не закрывать соединение, не фиксировать внешнюю транзакцию и не повторять её автоматически.

#### Scenario: Transaction ownership

- **WHEN** вызвана транзакционная отправка на активном соединении
- **THEN** управление commit/rollback и жизненным циклом соединения остаётся у приложения

#### Scenario: Connection error

- **WHEN** во время отправки во внешней транзакции произошла ошибка соединения
- **THEN** ошибка передаётся приложению без внутреннего повтора операции

### Requirement: Consistent message behavior

Обычный и транзакционный пути SHALL одинаково сериализовать сообщение и учитывать задержку.

#### Scenario: Delayed message

- **WHEN** задача поставлена через транзакцию с задержкой
- **THEN** после commit она не выполняется раньше вычисленного eta


### Requirement: Optional SQLAlchemy transaction input
Система SHALL предоставлять optional adapter для активных синхронных SQLAlchemy Connection/Session на PostgreSQL Psycopg 3, сохраняющий атомарность бизнес-данных и task publication и владение транзакцией у caller. Основной пакет SHALL работать без SQLAlchemy.

#### Scenario: Commit and rollback
- **WHEN** caller изменяет данные и публикует задачу через supported SQLAlchemy connection в одной активной DB transaction
- **THEN** commit сохраняет данные/задачу и доставляет NOTIFY, rollback отменяет данные/задачу/NOTIFY

#### Scenario: Caller lifecycle
- **WHEN** supported Session или Connection передан adapter
- **THEN** adapter не commit/rollback/close/autoflush и не retry caller transaction; дальнейший lifecycle управляется приложением

#### Scenario: Inactive or incompatible input
- **WHEN** передан Engine, async input, unsupported driver либо отсутствует активная DB transaction
- **THEN** adapter выдаёт понятную ошибку без fallback enqueue через отдельный pool

#### Scenario: Native publication behavior
- **WHEN** caller передал delay/deduplication options или использует nested transaction
- **THEN** поведение соответствует существующему transactional enqueue, rollback savepoint отменяет принадлежащую ему публикацию

#### Scenario: Base installation
- **WHEN** SQLAlchemy extra не установлен
- **THEN** core broker и Psycopg transactional APIs импортируются и работают

### Requirement: Async caller transaction publication

Система SHALL предоставлять отдельную awaitable публикацию на активной Psycopg 3 AsyncConnection в той же базе, что бизнес-данные и таблицы очереди. Она SHALL возвращать опубликованный либо ранее дедуплицированный Message, поддерживать delay и deduplication options синхронного пути, не выполнять commit/close или автоматические retries внешней транзакции. Синхронный API SHALL сохранять свой контракт.

#### Scenario: Visibility and commit
- **WHEN** приложение изменило бизнес-данные и выполнило await публикации в одной активной async транзакции
- **THEN** отдельное соединение не видит незавершённые изменения и не получает enqueue NOTIFY; после commit видны бизнес-данные и задача, доставляется уведомление

#### Scenario: External rollback
- **WHEN** приложение откатывает транзакцию после успешного await публикации
- **THEN** бизнес-данные, задача и принадлежащие этой публикации deduplication записи отменены, enqueue NOTIFY не доставляется

#### Scenario: Delay and duplicate
- **WHEN** передана задержка либо повторный действующий ключ дедупликации
- **THEN** задержка сохраняет delayed queue/ETA синхронного пути; duplicate возвращает исходный Message без второй задачи, второго уведомления и enqueue hooks повторной публикации

#### Scenario: Incompatible or inactive connection
- **WHEN** передано синхронное соединение, неподдерживаемый тип либо async соединение вне активной транзакции
- **THEN** вызов завершается понятной ошибкой до публикации без fallback на broker pool

### Requirement: Async errors and cancellation ownership

Async публикация SHALL передавать ошибки и отмену coroutine приложению без retry, подавления отмены, закрытия соединения или завершения внешней транзакции. Внутренняя составная публикация с дедупликацией SHALL использовать savepoint для атомарности своих SQL операций. Hooks SHALL описывать SQL публикацию, а не внешний commit, и оставаться синхронными.

#### Scenario: Database error
- **WHEN** запись сообщения завершается ошибкой PostgreSQL
- **THEN** ошибка передаётся caller; внутренняя составная публикация откатывает свой savepoint, решение о внешнем rollback остаётся у caller

#### Scenario: Cancellation during SQL
- **WHEN** caller отменяет coroutine во время SQL и выходит из внешней транзакции с отменой
- **THEN** отмена достигает caller, задача/ключ/NOTIFY не фиксируются; соединение не закрывается брокером и допускает использование после выполненного caller rollback

#### Scenario: Hook timing
- **WHEN** await публикации успешно завершился, а caller впоследствии откатил транзакцию
- **THEN** уже вызванные enqueue hooks не обещают commit и не отменяются; сообщение в очереди отсутствует
