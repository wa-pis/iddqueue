## Purpose

Отменять задачи до начала исполнения и предоставлять выполняющемуся actor добровольную проверку запроса отмены.

## ADDED Requirements

### Requirement: Cancellation lifecycle

Отмена SHALL идемпотентно предотвращать старт queued/delayed/prefetched задачи и отличаться от ошибки actor. Для выполняющейся задачи SHALL сохраняться запрос отмены, доступный через cooperative API; принудительное прерывание не гарантируется.

#### Scenario: Cancel before start
- **WHEN** отмена зафиксирована до разрешения старта actor
- **THEN** actor не вызывается, задача получает терминальный cancelled status

#### Scenario: Execution wins race
- **WHEN** actor получил разрешение старта раньше отмены
- **THEN** API сообщает запрос отмены выполняющейся задачи; actor сам проверяет флаг

#### Scenario: Cancellation result
- **WHEN** запрошен результат отменённой задачи
- **THEN** клиент получает документированную ошибку отмены без ожидания timeout

#### Scenario: Cancel twice
- **WHEN** отменена уже cancelled задача
- **THEN** результат идемпотентен; задача не возвращается в queued

#### Scenario: Missing or completed task
- **WHEN** отмена запрошена для отсутствующей либо завершённой задачи
- **THEN** API явно сообщает missing либо terminal без изменения результата
