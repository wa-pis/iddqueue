## Local verification

Удалены 9 obsolete files/assets: CHANGELOG symlink, pyrightconfig.json (include отсутствующего dramatiq_pg), tests/func/docker-compose.yml (Poetry), его entrypoint.sh, unused tests/postgresql-conf.sh и 4 upstream logo files. Active references/callers проверены rg. LICENSE/credits, docs/changelog.rst, perf scripts, docs Makefile и OpenSpec history сохранены.
Root Compose больше не монтирует partial DDL; docs используют CLI для полного storage. Исправлены install/dev commands, current public visibility и PyPI status в AGENTS/config. Published RC artifacts/history не менялись.

- Python 3.13.14 / PostgreSQL 14.20 dedicated localhost:55432, свежая DB iddqueue_cleanup.
- `iddqueue init` + `python tests/pypsql < tests/func/schema.sql`: exit 0, полная schema и test witness созданы без partial init.
- `uv run --locked --extra binary --extra monitoring --group fastapi-example pytest tests/unit tests/func`: 147 passed, 46.98s, exit 0. UV_PROJECT_ENVIRONMENT=/tmp/iddqueue-rc-env, UV_CACHE_DIR=/tmp/iddqueue-uv-cache, PG* указывают dedicated DB; PATH содержит выбранный venv.
- Ruff iddqueue/unit/func/example/scripts/quickstart/examples: passed.
- docs checker: exit 0; uv lock --check: exit 0; strict OpenSpec 19/19; git diff --check: exit 0.
- Compose YAML parsed with Psych: syntax valid. Docker binary присутствует, Compose plugin недоступен (`docker compose config --quiet`: unknown flag); container runtime не проверялся. Эквивалентный fresh PostgreSQL init/test flow проверен нативно выше.
- Packaging/runtime не менялись, build отдельно не повторялся; actual GitHub release gate выполняет build/install checks.
- Свежая тестовая DB удалена, dedicated PostgreSQL остановлен.

## Remote verification

Signed commit ef611d2be8fec0b2cc51cebc84a1cc173420be52 отправлен в main; git verify-commit: Good SSH signature.
[Tests 37233116835](https://github.com/wa-pis/iddqueue/actions/runs/37233116835): success 6/6, full release gate/build/installed acceptance.
Jobs: 3.10/PG18 111526796998, 3.13/PG18 111526797120, 3.14/PG14 111526797170, 3.13/PG14 111526797180, 3.14/PG18 111526797183, 3.10/PG14 111526797315 — все success.
No delta specs (skip_specs). Archive bookkeeping commit не меняет runtime/tooling кандидата.
