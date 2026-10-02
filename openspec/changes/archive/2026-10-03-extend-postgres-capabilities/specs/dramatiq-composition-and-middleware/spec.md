## ADDED Requirements

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
