## Why

Security review выявил all-interface publication локальной демонстрационной БД с известным postgres password. Это low finding: фактическая внешняя доступность не установлена.

## What Changes

- Привязать example PostgreSQL port к 127.0.0.1; удалённый доступ требует явной настройки оператора.

## Capabilities

### New Capabilities
Нет.

### Modified Capabilities
Нет, только local example configuration; skip_specs: true.

## Impact

examples/postgres/compose.yml, без runtime/dependencies/schema изменений.
