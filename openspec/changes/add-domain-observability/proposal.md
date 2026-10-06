## Why

Нужно наблюдать backlog и работу очередей по доменам без импорта actor modules. Уже существуют queue_statistics и optional Prometheus collector; их следует расширить минимально.

## What Changes

- Доменные snapshots с фильтром по явным именам и объединением основной/DQ очереди.
- Optional domain-labelled Prometheus gauges, переиспользующие snapshot; existing queue metrics сохраняются.
- Документировать стандартные Dramatiq processing counters/histograms и их доменную группировку по queue labels без новых runtime collectors.
- Различать retained done/rejected snapshots и накопительные processing counters.

## Capabilities

### Modified Capabilities
- queue-observability: доменная агрегация и явный контракт метрик.

## Impact

metrics/helpers, monitoring, tests/docs; без новой таблицы, domain registry, daemon или обязательной зависимости. RC3 не изменяется.
