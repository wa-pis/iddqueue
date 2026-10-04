#!/bin/sh
# Requires a prepared, dedicated PostgreSQL: functional tests terminate sessions.
set -eu
cd "$(dirname "$0")/.."
: "${IDDQUEUE_TEST_DATABASE:?Set IDDQUEUE_TEST_DATABASE=dedicated for an isolated test instance}"
[ "$IDDQUEUE_TEST_DATABASE" = dedicated ] || exit 1
: "${PGHOST:?Set PGHOST for the dedicated test instance}"
: "${PGDATABASE:?Set PGDATABASE for the dedicated test database}"
PYTHON=${PYTHON:-python}
POETRY=${POETRY:-poetry}
"$PYTHON" - <<'PY'
import psycopg
with psycopg.connect("") as conn:
    for table in ("dramatiq.queue", "functest.witness"):
        assert conn.execute("SELECT to_regclass(%s)", (table,)).fetchone()[0], f"Prepare test table {table}"
PY
"$POETRY" check
"$POETRY" run ruff check iddqueue tests/unit tests/func example.py scripts
"$POETRY" run pytest tests/unit tests/func
"$PYTHON" scripts/check_docs.py
openspec validate --all --strict
"$POETRY" build
# Select this distribution only; unrelated historical artifacts may exist in dist/.
"$PYTHON" scripts/check_license.py dist/iddqueue-*.whl dist/iddqueue-*.tar.gz
"$PYTHON" scripts/check_package.py dist/iddqueue-*.whl
"$PYTHON" - <<'PY'
import hashlib
import subprocess
from pathlib import Path
print("Checked commit:", subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip())
print("Working tree:", subprocess.check_output(["git", "status", "--short"], text=True).strip() or "clean")
for path in sorted(Path("dist").glob("iddqueue-*")):
    print("SHA256:", hashlib.sha256(path.read_bytes()).hexdigest(), path)
PY
