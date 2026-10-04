## Why

Пользователь запросил очистку репозитория от ненужного legacy. Найдены obsolete Poetry runner, устаревший typechecker config и неиспользуемые assets; optional Compose создаёт неполную схему.

## What Changes

- Удалить tests/func/docker-compose.yml и его entrypoint.sh, неиспользуемый postgresql-conf.sh, stale pyrightconfig.json, дублирующий CHANGELOG symlink и четыре unused upstream logo assets.
- Сохранить LICENSE/credits, исторический docs/changelog.rst, полезные perf scripts, runtime/tests, uv/OpenSpec и docs checker.
- Корневой Compose оставляет чистый dedicated PostgreSQL: schema init через актуальный CLI из dev instructions.
- Исправить текущие AGENTS/OpenSpec сведения о public visibility и публикации; архивные факты сохраняются.
- Исправить stale installation/development команды: published RC и fastapi-example group для полного suite.

## Capabilities

### New Capabilities

Нет.

### Modified Capabilities

Нет: cleanup docs/tooling, skip_specs=true.

## Impact

Только неиспользуемые legacy files, optional development Compose и документация. Published RC artifacts/история не меняются.
