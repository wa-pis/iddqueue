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
