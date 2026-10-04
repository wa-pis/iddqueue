## Why

Пользователь выбрал uv вместо Poetry. Проект уже использует PEP 621 metadata, но dev dependencies, build backend, lockfile, CI и документация остаются привязаны к Poetry; переход должен сохранить установленный wheel, LICENSE, SQL resources и полный release gate.

## What Changes

- uv.lock вместо poetry.lock, стандартная dependency-groups.dev вместо tool.poetry.group.
- uv sync/run/build, locked CI и release checks без Poetry.
- Native uv_build с явным root module iddqueue; проверить содержимое wheel/sdist.
- Обновить актуальные README/docs/CONTRIBUTING/AGENTS/config, сохраняя исторические архивные evidence.
- Сохранить Python/PostgreSQL matrix, extras binary/monitoring, runtime constraints и отдельную публикацию.

## Capabilities

### New Capabilities

Нет.

### Modified Capabilities

- `project-maintenance`: воспроизводимое uv-окружение и неизменяемый lockfile при проверках.

## Impact

pyproject.toml, uv.lock, poetry.lock, CI, scripts/check_release.sh, актуальная документация, AGENTS.md и openspec/config.yaml. Runtime/SQL/public API не меняются. Разрешение зависимостей может дать новые версии: изменения зафиксировать отдельно в evidence, не объявлять незапрошенные security findings исправленными. Публикация и tags вне scope.
