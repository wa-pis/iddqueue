# postgres-rate-limits-and-barriers Specification

## Purpose

Лимиты и завершение групп через PostgreSQL: определить проверяемый контракт этой возможности для PostgreSQL-проекта и совместимости с Dramatiq.

## Requirements

### Requirement: Distributed limits

Backend SHALL координировать стандартные лимитеры Dramatiq между процессами с атомарными изменениями счётчиков и TTL.

#### Scenario: Concurrent capacity

- **WHEN** несколько workers одновременно пытаются занять лимит из пяти слотов
- **THEN** до освобождения или истечения TTL успешно занимают не более пяти слотов

#### Scenario: Window limit

- **WHEN** workers конкурируют за общий лимит окна
- **THEN** атомарная проверка суммы не допускает превышения установленного лимита

#### Scenario: Expired key

- **WHEN** TTL ключа истёк
- **THEN** ключ трактуется как отсутствующий при новой операции

### Requirement: Barrier completion

Backend SHALL поддерживать стандартные барьеры и callback завершения группы через middleware Dramatiq.

#### Scenario: Group callback

- **WHEN** все задачи группы успешно завершаются без повторной доставки
- **THEN** стандартный GroupCallbacks ставит callback в очередь после достижения барьера

### Requirement: Durable notification wait

Ожидание SHALL учитывать таймаут в миллисекундах и состояние события, чтобы не зависеть только от доставки NOTIFY.

#### Scenario: Event before wait

- **WHEN** событие опубликовано до подписки и его TTL ещё действует
- **THEN** ожидание обнаруживает опубликованное событие

#### Scenario: Wait timeout

- **WHEN** событие не появляется до заданного срока
- **THEN** ожидание возвращает признак отсутствия события без бесконечного блокирования
