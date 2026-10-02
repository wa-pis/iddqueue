# postgres-queue-control Specification

## Purpose

Долговременно приостановить обработку логической очереди и возобновить её без потери принятых сообщений.

## Requirements

### Requirement: Durable pause and resume

При включённом queue control у всех участвующих workers пауза SHALL сохраняться в PostgreSQL и запрещать начало новых actor executions в обычной и delayed очереди; отправка SHALL продолжаться. Уже начавшие выполнение actors SHALL завершаться обычным образом.

#### Scenario: Prefetched task
- **WHEN** очередь приостановлена до старта prefetched задачи
- **THEN** actor не начинается, сообщение сохраняется для возобновления

#### Scenario: Restart while paused
- **WHEN** workers перезапущены во время паузы
- **THEN** очередь остаётся приостановленной

#### Scenario: Resume
- **WHEN** очередь возобновлена
- **THEN** доступные queued задачи получают wakeup и выполняются; ETA сохраняется

#### Scenario: Queue isolation
- **WHEN** приостановлена одна очередь
- **THEN** другие очереди продолжают обработку


#### Scenario: Authorized actor
- **WHEN** разрешающая start gate транзакция завершилась до pause
- **THEN** actor может завершиться обычным образом; pause не прерывает уже разрешённое исполнение

#### Scenario: Start gate database failure
- **WHEN** проверка разрешения старта не может прочитать PostgreSQL
- **THEN** actor не запускается и задача откладывается без расходования retry budget
