## Why

Пользователь одобрил три находки Ponytail audit: неиспользуемый watch extra, redundant argparse defaults и Makefile wrapper.

## What Changes

Убрать dev dramatiq[watch] (runtime Dramatiq остаётся), пересчитать uv.lock; Watchdog остаётся транзитивной зависимостью MkDocs. Удалить redundant action=store и совпадающие dest. Удалить docs/Makefile, сохранив scripts/check_docs.py и release gate.

## Capabilities

Публичные contracts/specs не меняются.

## Impact

Только development dependencies и CLI boilerplate; CLI parsing сохраняется.
