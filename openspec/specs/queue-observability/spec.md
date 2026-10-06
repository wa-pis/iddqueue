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
