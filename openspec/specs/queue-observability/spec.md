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
