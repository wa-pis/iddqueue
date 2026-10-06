## Why

Пользователь запросил graceful restart/завершение. Штатный Dramatiq уже обрабатывает SIGHUP/SIGTERM; требуется явная инструкция и evidence выполнения активных задач.

## What Changes

- Документировать native signals, shutdown timeout и контейнерный grace period.
- Проверить in-flight result, prefetched backlog, новые worker PIDs после SIGHUP и connections0 после SIGTERM.

## Capabilities

### New Capabilities
Нет.

### Modified Capabilities
Нет: existing native lifecycle documentation, skip_specs: true.

## Impact

docs/deployment-guide.md и ссылки; без отдельной restart API, subprocess manager или runtime изменений.
