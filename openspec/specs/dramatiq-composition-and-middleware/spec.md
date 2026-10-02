# dramatiq-composition-and-middleware Specification

## Purpose

Совместимость со стандартными возможностями Dramatiq: определить проверяемый контракт этой возможности для PostgreSQL-проекта и совместимости с Dramatiq.

## Requirements

### Requirement: Task composition

Брокер SHALL поддерживать стандартные pipelines и groups Dramatiq с получением результатов.

#### Scenario: Pipeline

- **WHEN** запущена цепочка из двух actors с передачей результата
- **THEN** вторая задача получает результат первой, а итоговый результат доступен

#### Scenario: Group

- **WHEN** запущена группа независимых задач с сохранением результатов
- **THEN** все задачи выполняются и результаты доступны стандартным group API

### Requirement: Async actor compatibility

С подключённым AsyncIO middleware SHALL выполняться стандартные async actors.

#### Scenario: Coroutine actor

- **WHEN** отправлена задача async actor со стандартным middleware
- **THEN** корутина завершается и её результат доступен через PostgreSQL Results

### Requirement: Retry exhaustion callback

При исчерпании retries SHALL работать стандартный on_retry_exhausted.

#### Scenario: Retries exhausted

- **WHEN** задача исчерпала установленный бюджет повторов
- **THEN** назначенный actor получает callback по контракту Dramatiq

### Requirement: Standard delay input

Отправка через стандартный Actor API SHALL принимать timedelta задержки.

#### Scenario: Timedelta delay

- **WHEN** задача отправлена через send_with_options с delay=timedelta(seconds=1)
- **THEN** она выполняется не ранее установленной задержки
