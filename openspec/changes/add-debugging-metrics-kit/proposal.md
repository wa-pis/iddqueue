## Why

Для отладки нужны готовые показатели ошибок/retries/отклонения, backlog/возраста и длительности. Уже существуют native Dramatiq metrics и domain SQL gauges; пользователю нужен штатный recipe/dashboard без нового runtime.

## What Changes

Добавить troubleshooting guide, importable Grafana JSON и runnable PostgreSQL exporter example. Проверить dashboard queries/labels на существующих metrics, отдельно объяснить attempts vs retained states, delayed/prefetched/inprogress, p50/p95 и отсутствие данных. Monitoring остаётся optional; defaults broker не меняются.

## Capabilities

### Modified Capabilities
- queue-observability: стандартный набор отладочных recipes/dashboard.

## Impact

Docs/examples/tests; без новой storage schema, middleware, обязательной зависимости, HTTP runtime внутри пакета или автоматических alert thresholds. Новые возможности development checkout, published RC3 неизменен.
