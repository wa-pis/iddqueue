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
