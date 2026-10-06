## ADDED Requirements

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
