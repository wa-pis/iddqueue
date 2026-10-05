# Evidence

2026-10-05: example.py перенесён в tests/func/actors.py; удалён unused producer/main/pdb/debugger, actors/configuration сохранены. Imports и WorkerManager используют tests.func.actors. Явные package markers добавлены для spawn imports.

Compose перенесён byte-for-byte в examples/postgres/compose.yml (cmp с HEAD подтверждён), active docs обновлены. Семь .agents/skills файлов исключены из Git через rm --cached; локальные копии существуют и игнорируются через .agents/. AGENTS/OpenSpec остаются tracked.

Local: 147 tests passed in 47.99s, Python 3.13.14 / dedicated PostgreSQL 14.20. Ruff, uv lock --check, docs checker, strict MkDocs и OpenSpec 19/19 passed. Compose engine не запускался (локальный plugin отсутствует); перенос конфигурации точный. Packaging/runtime package не менялись.

Remote CI/Pages pending.
