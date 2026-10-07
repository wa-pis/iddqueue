# Проверки async transactional enqueue — 2026-10-07

## Implementation

Отдельные async single/batch методы на caller AsyncConnection; общие ENQUEUE SQL/serialization, dedup upsert SQL/validation и batch bounds. Внешняя транзакция не commit/close/retry; dedup/batch используют native async savepoint. Sync API, SQLAlchemy adapter и DDL сохранены. Hooks синхронны, не означают внешний commit.

## Local verification

- Python 3.13.14 / Psycopg 3 / выделенный PostgreSQL 14.20: PGHOST=127.0.0.1 PGPORT=55433 PGUSER=postgres PGDATABASE=postgres IDDQUEUE_TEST_DATABASE=dedicated.
- `uv run --locked --extra binary --extra monitoring --group fastapi-example --group docs pytest tests/unit tests/func`: **200 passed in 55.90s**; UV_PROJECT_ENVIRONMENT=/tmp/iddqueue-docsite-env и UV_CACHE_DIR=/tmp/iddqueue-uv-cache, CLI PATH включает окружение.
- Целевые async/sync transactional, batch/dedup tests: **38 passed in 1.42s**. Девять новых functional cases включают commit/rollback business/task/key/NOTIFY, quoted schema/prefix, delay/duplicate/mixed batch/nested rollback/hooks, неправильный input/idle/лимиты, SQL и validation failure после первой записи, no retry и cancellation.
- Отмена: trigger/advisory lock + pg_stat_activity подтверждают блокировку конкретного SQL, параллельная monitor coroutine продолжает работу; отмена single statement передаётся caller, outer transaction откатывается через native Rollback context и соединение повторно используется. Mixed batch пишет первый message/key до блокировки второго; отмена откатывает savepoint, caller сохраняет предыдущую business запись. Нет частичных task/key или NOTIFY; deadlines 5/10 секунд, без случайной задержки.
- `python docs/async-transaction.py`: business commit + actor result подтверждены, worker остановлен и isolated schema удалена. Рецепт добавлен в CI release gate после pytest.
- Required locked Ruff плюс scripts/examples/async recipe: passed; `sh -n scripts/check_release.sh` passed.
- `uv lock --check` с UV_CACHE_DIR=/tmp/iddqueue-uv-cache passed (55 packages); первоначальный запуск с default cache был отклонён sandbox, не считается pass.
- `python scripts/check_docs.py`, `mkdocs build --strict`, `openspec validate --all --strict`: passed, OpenSpec 20/20.
- Первоначальная расширенная целевая проверка: 37 passed / 1 failed из-за explicit conn.rollback() внутри Psycopg transaction context в самом тесте. Исправлено на штатный Rollback context; повторная целевая и полный набор passed.
- Packaging metadata/dependencies не менялись. Local build не запускался; immutable dist/0.13.0rc4 не перезаписывался. GitHub matrix выполняет полный build/LICENSE/installed-wheel release gate в своих isolated workspaces.

## Remote verification

Ожидается после подписанного feature commit и push. Новые tag/release/PyPI публикации не выполняются; документы явно обозначают development API вне RC4.
