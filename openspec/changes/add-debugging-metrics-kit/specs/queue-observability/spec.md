## ADDED Requirements

### Requirement: Standard debugging metrics kit
Проект SHALL предоставлять готовую optional monitoring инструкцию и dashboard для backlog, возраста готовой задачи, отложенных/выполняющихся tasks, ошибок/retries/terminal rejects и p50/p95 длительности по выбранным доменам. Показатели SHALL переиспользовать существующие metrics и различать attempts и retained rows; counters SHALL обрабатываться с учётом reset, histogram quantiles — вычисляться после aggregation buckets.

#### Scenario: Failed and retried actor
- **WHEN** актор ошибается и повторяется до отклонения
- **THEN** kit показывает отдельные errors/retries/rejects и не называет число ошибочных attempts числом уникальных failed tasks

#### Scenario: Backlog and execution
- **WHEN** есть ready/future prefetched tasks
- **THEN** backlog/age/scheduled показываются SQL gauges, actual executing берётся из native inprogress, а consumed не считается executing

#### Scenario: Scoped dashboard
- **WHEN** пользователь выбирает datasource, jobs и домен
- **THEN** dashboard использует выбранные источники, объединяет domain main/DQ transport и не суммирует дублированные storage snapshots

#### Scenario: Missing metrics
- **WHEN** exporter недоступен либо нет наблюдений длительности
- **THEN** инструкция отличает no data от zero; kit не включает monitoring автоматически и не добавляет payload/exception labels
