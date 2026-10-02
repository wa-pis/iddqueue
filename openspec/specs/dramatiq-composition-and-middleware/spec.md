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

### Requirement: Remaining middleware compatibility

Стандартные AgeLimit, TimeLimit, ShutdownNotifications, Callbacks и CurrentMessage SHALL работать с PostgreSQL broker согласно контрактам Dramatiq без собственных копий middleware.

#### Scenario: Expired message
- **WHEN** AgeLimit отклоняет просроченную задачу
- **THEN** actor не вызывается; сообщение не застревает consumed, locks освобождаются

#### Scenario: Time limit
- **WHEN** TimeLimit прерывает CPU-bound actor в поддерживаемом CPython
- **THEN** Retries/Results отражают ошибку и сообщение не остаётся заблокированным

#### Scenario: Shutdown notification
- **WHEN** notify_shutdown actor получает Shutdown при остановке
- **THEN** идемпотентная задача возвращается либо завершается по штатному контракту

#### Scenario: Success and failure callbacks
- **WHEN** actor завершён успешно либо окончательной ошибкой
- **THEN** назначенный callback получает данные по стандартному контракту

#### Scenario: Current message
- **WHEN** actor использует CurrentMessage
- **THEN** виден правильный message_id/options; контекст не переходит соседней задаче


#### Scenario: Failure callback during retry
- **WHEN** actor падает и стандартный Retries назначает повтор
- **THEN** on_failure получает callback для этой попытки; on_retry_exhausted остаётся отдельным terminal callback
