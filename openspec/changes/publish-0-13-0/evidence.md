## Local release gate

Дата: 2026-10-07. Python 3.13.14, выделенный PostgreSQL 14.20 /tmp/iddqueue-domains-pg, port55433/max_connections120, databasepostgres. Gate scripts/check_release.sh exit0, лог /tmp/iddqueue-stable-gate.log. PGHOST=127.0.0.1 PGPORT=55433 PGUSER=postgres PGDATABASE=postgres IDDQUEUE_TEST_DATABASE=dedicated UV_PROJECT_ENVIRONMENT=/tmp/iddqueue-docsite-env UV_CACHE_DIR=/tmp/iddqueue-uv-cache PYTHON=/tmp/iddqueue-docsite-env/bin/python UV=/opt/homebrew/bin/uv.

200 tests passed; Ruff, uv lock/sync/pip check, async actor recipe, strict docs/OpenSpec20/20, build/LICENSE, isolated base/monitoring/SQLAlchemy wheel installs и quickstart result5/cleanup passed. uv.lock изменил только root version, dependencies сохранены. Побайтовое сравнение wheel RC5/stable: все23 runtime/SQL files identical. Gate выполнил проверку dirty release tree поверх7d2d206; candidate SHA будет записан после signed commit и подтверждён remote CI.

Предыдущий security diff RC4..RC5: 20 paths,0findings; новый runtime diff пуст. Новый полный security scan не выполнялся.

## Artifacts

eaa5e6c855485249908c67eaab24ddfd71b762f2030cefe7cba31f5ec68c1826  iddqueue-0.13.0-py3-none-any.whl
8531940c89b29e88161e547f1d441b13f52f3c01a8330de315a91862356b4ddb  iddqueue-0.13.0.tar.gz

Remote CI и publication ещё не проверены.
