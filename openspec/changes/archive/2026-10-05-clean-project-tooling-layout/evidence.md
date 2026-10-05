# Evidence

2026-10-05: example.py перенесён в tests/func/actors.py; удалён unused producer/main/pdb/debugger, actors/configuration сохранены. Imports и WorkerManager используют tests.func.actors. Явные package markers добавлены для spawn imports.

Compose перенесён byte-for-byte в examples/postgres/compose.yml (cmp с HEAD подтверждён), active docs обновлены. Семь .agents/skills файлов исключены из Git через rm --cached; локальные копии существуют и игнорируются через .agents/. AGENTS/OpenSpec остаются tracked.

Local: 147 tests passed in 47.99s, Python 3.13.14 / dedicated PostgreSQL 14.20. Ruff, uv lock --check, docs checker, strict MkDocs и OpenSpec 19/19 passed. Compose engine не запускался (локальный plugin отсутствует); перенос конфигурации точный. Packaging/runtime package не менялись.

Remote CI/Pages pending.

Signed implementation commit: 220c52f081b332680d4b61b124f3e6b12fecba17; SSH signature verified. Tests 37353269772 success 6/6 (Python 3.10/3.13/3.14 × PostgreSQL 14/18), including full release gate/build/LICENSE/installed wheel acceptance. Documentation 37353269808 build/deploy success; live walkthrough contains the new -f Compose path. git ls-files .agents .codex empty; working tree clean after implementation commit. All tasks complete, no delta specs to sync.
