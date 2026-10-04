## Context

См. proposal.md. PEP 621 runtime/extras уже отделены от Poetry. Текущие dev dependencies имеют Poetry dict extras, семь SQL ресурсов включены через tool.poetry; check_release.sh вызывает poetry check/run/build, wheel acceptance использует независимые venv/pip. uv установлен локально; сохранить acceptance независимым от frontend.

## Goals / Non-Goals

**Goals:** одна uv-команда setup, locked проверка, сборка без Poetry, прежний release gate.

**Non-Goals:** runtime refactor, смена Python support, смена CLI/package, публикация, новые контейнерные pipelines, отдельный dependency upgrade проект.

## Decisions

Использовать dependency-groups.dev и существующие PEP 621 extras; uv sync --locked --extra binary --extra monitoring. Run checks с явными extras или --no-sync после locked sync, чтобы очередной uv run не удалял monitoring. Не использовать --frozen как замену проверки актуальности metadata.

Сборка uv_build (актуальный совместимый version range проверить по официальной документации), module-root="", module-name="iddqueue". Удалить tool.poetry и poetry-core; проверить штатное включение семи SQL файлов и полного LICENSE вместо предположения об auto-discovery. Если native backend не обеспечивает metadata/resources, сначала доказать конкретную несовместимость и выбрать минимальную явную настройку, не менять формат поставки незаметно.

CI сохраняет setup-python matrix и использует официальный setup-uv с фиксированной версией uv; установленный interpreter должен совпадать с matrix. Lock check вместо poetry check, build/metadata/license acceptance вместо формального TOML-only check. scripts/check_release.sh остаётся единственным gate без публикации; не добавлять несколько wrappers.

Сравнить poetry.lock и uv.lock версии пакетов; по возможности сохранить действующие версии без случайного upgrade. Не переносить Poetry runtime/CLI в новое venv. Архивные OpenSpec/evidence сохраняют исторические команды; актуальные инструкции и config обновляются.

## Risks / Trade-offs

- Потеря LICENSE/SQL при backend смене → build обеих форматов, check_license и installed-wheel smoke/quickstart вне checkout.
- uv run пересинхронизирует extras → единый locked sync со всеми нужными extras и согласованная run policy.
- Переиспользование старого .venv скрывает setup bug → чистое отдельное uv environment для acceptance.
- Resolution drift → список changed versions в evidence и проверка полной CI matrix; без обещаний устранения Pygments advisory до проверки конкретной версии.

## Migration Plan

Зафиксировать старые locks/metadata через Git; конвертировать groups/backend и lock, проверить clean sync. Перевести gate/CI/docs/AGENTS. Выполнить полный набор на выделенном PG, build/LICENSE/wheel base+monitoring/quickstart, strict OpenSpec; commit/push, реальный CI. Rollback — revert tooling commit и пересоздание окружения по старому lock; SQL/data migration не нужна.
