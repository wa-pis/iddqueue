## Context

--watch не используется тестами/документацией. argparse store — default; dest schemaname/prefix выводится из flags. Makefile только вызывает check_docs.py и не используется CI.

## Decisions

Удалить одну dev extra requirement; Watchdog сохраняется, поскольку нужен MkDocs; runtime Dramatiq и остальные версии lock сохранить. Удалять только redundant parser options, dest=url/purge_maxage/recover_minage сохранить. Native scripts/check_docs.py остаётся entry point.

## Verification

Ruff, uv lock --check, полный unit/func suite на выделенном PostgreSQL, strict docs/MkDocs/OpenSpec. Signed commit/push, actual six-job CI и Documentation; evidence/archive.
