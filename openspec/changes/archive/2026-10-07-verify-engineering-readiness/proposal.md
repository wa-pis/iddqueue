## Why

Перед следующим RC необходимо закрыть пробелы в evidence: нестабильные retry/delay tests, новые API из wheel, реальный Grafana render и ограниченный multi-worker soak.

## What Changes

- Повторить timing regressions, проследить причины и записать находки без молчаливого подавления failures.
- Собрать development wheel в отдельной временной директории и проверить Domain/SQLAlchemy/metrics вместе вне checkout.
- Импортировать dashboard в локальный Grafana и проверить variables/render/data/no-data.
- Выполнить ограниченный multi-worker прогон с retry/restart, connection/retention observations.

## Capabilities

### New Capabilities
Нет.

### Modified Capabilities
Нет: verification existing contracts, skip_specs: true. Runtime fixes при подтверждённой необходимости оформляются отдельным change.

## Impact

Evidence и roadmap, временные окружения/выделенный PG. Без публикации, новых зависимостей проекта или изменений release assets.
