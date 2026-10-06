# queue-observability Specification

## Purpose

Метрики PostgreSQL-очереди: определить проверяемый контракт этой возможности для PostgreSQL-проекта и совместимости с Dramatiq.

## Requirements

### Requirement: Queue health statistics

Статистика SHALL показывать состояние каждой выбранной очереди и возраст старейшего ожидающего сообщения.

#### Scenario: Backlog visibility

- **WHEN** в очереди есть ожидающие сообщения
- **THEN** статистика показывает их число и неотрицательный возраст старейшего

#### Scenario: Empty queue

- **WHEN** очередь пуста
- **THEN** статистика возвращает нулевые показатели без ошибки

### Requirement: Optional monitoring

Prometheus-интеграция SHALL включаться явно; основной брокер SHALL работать без установки мониторингового extra.

#### Scenario: No monitoring dependency

- **WHEN** пакет установлен без extra мониторинга
- **THEN** брокер импортируется и выполняет задачи

#### Scenario: Metrics scrape

- **WHEN** collector включён и PostgreSQL доступен
- **THEN** scrape возвращает PostgreSQL-метрики очереди; стандартный middleware предоставляет метрики обработки


### Requirement: Domain queue snapshots
Система SHALL предоставлять JSON-compatible snapshot по доменам, агрегируя основную очередь и её delayed очередь, с counts по state, ready, scheduled и возрастом старейшего готового сообщения. Выбор доменов SHALL не требовать импорта actors.

#### Scenario: Main and delayed queues
- **WHEN** выбран billing с сообщениями в billing и billing.DQ
- **THEN** возвращён один billing snapshot без двойного счёта, scheduled включает future prefetched messages, возраст — максимальный среди готовых queued messages

#### Scenario: Empty requested domain
- **WHEN** явно выбран домен без сохранённых сообщений
- **THEN** возвращены нулевые показатели

#### Scenario: Namespace and dotted names
- **WHEN** выбран домен shipping.eu в заданных schema/prefix
- **THEN** агрегируются shipping.eu и shipping.eu.DQ только в выбранной namespace

### Requirement: Domain metrics semantics
Optional monitoring SHALL предоставлять доменные gauges без изменения существующих queue metrics; retained states SHALL не представляться накопительными counters, а consumed SHALL не обозначать точное число выполняющихся actors. Processing counters/histograms SHALL документироваться отдельно на основе существующего middleware.

#### Scenario: Purged retained messages
- **WHEN** done/rejected сообщения удалены retention
- **THEN** snapshot gauges уменьшаются, документация не предлагает трактовать их как processing throughput

#### Scenario: Optional scrape
- **WHEN** collector зарегистрирован и затем выполнен scrape
- **THEN** регистрация не подключается к БД, scrape возвращает domain-labelled gauges и не требует импорта actor modules


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
