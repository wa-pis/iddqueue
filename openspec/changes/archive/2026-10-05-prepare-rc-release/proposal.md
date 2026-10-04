## Why

Реализованные возможности и FastAPI-пример проверены, но текущая версия 0.13.0 не обозначает предварительный выпуск. Нужен воспроизводимый кандидат 0.13.0rc1 с release notes, проверенными артефактами и evidence конкретного commit.

## What Changes

- Установить 0.13.0rc1 в package metadata и uv.lock; сохранить runtime API и зависимости.
- Подготовить notes первого IDDQueue RC, список миграционных действий и известных ограничений, сохранив attribution и LICENSE.
- Устранить известный dev-only advisory Pygments минимальным обновлением lock до исправленной версии; проверить docs.
- Проверить точные RC wheel/sdist, чистую установку и CLI version, полный release gate и GitHub matrix.
- Зафиксировать кандидата и checksums. Tag, GitHub release и загрузка в PyPI/TestPyPI остаются отдельным шагом после подготовки.

## Capabilities

### New Capabilities

Нет.

### Modified Capabilities

Нет: это подготовка release metadata, docs и tooling; skip_specs=true. Существующие project-distribution/project-maintenance контракты сохраняются.

## Impact

pyproject.toml, uv.lock, CHANGELOG, release notes/guide, минимальная коррекция выбора артефактов в release gate при необходимости, OpenSpec evidence. Новые runtime возможности, schema migration и публикация не входят в подготовку.
