## Purpose

Долговременно приостановить обработку логической очереди и возобновить её без потери принятых сообщений.

## ADDED Requirements

### Requirement: Durable pause and resume

Пауза SHALL сохраняться в PostgreSQL и запрещать начало новых actor executions в обычной и delayed очереди; отправка SHALL продолжаться. Уже начавшие выполнение actors SHALL завершаться обычным образом.

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
