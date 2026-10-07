#!/bin/sh
# Requires a prepared, dedicated PostgreSQL: functional tests terminate sessions.
set -eu
cd "$(dirname "$0")/.."
: "${IDDQUEUE_TEST_DATABASE:?Set IDDQUEUE_TEST_DATABASE=dedicated for an isolated test instance}"
[ "$IDDQUEUE_TEST_DATABASE" = dedicated ] || exit 1
: "${PGHOST:?Set PGHOST for the dedicated test instance}"
: "${PGDATABASE:?Set PGDATABASE for the dedicated test database}"
PYTHON=${PYTHON:-python}
UV=${UV:-uv}
"$UV" lock --check
"$UV" sync --locked --extra binary --extra monitoring --group fastapi-example --group docs
"$PYTHON" - <<'PY'
import psycopg
with psycopg.connect("") as conn:
    for table in ("dramatiq.queue", "functest.witness"):
        assert conn.execute("SELECT to_regclass(%s)", (table,)).fetchone()[0], f"Prepare test table {table}"
PY
"$UV" pip check --python "$("$UV" run --no-sync python -c 'import sys; print(sys.executable)')"
"$UV" run --no-sync ruff check iddqueue tests/unit tests/func scripts docs/quickstart.py docs/async-transaction.py examples
"$UV" run --no-sync pytest tests/unit tests/func
"$UV" run --no-sync python docs/async-transaction.py
"$PYTHON" scripts/check_docs.py
"$UV" run --no-sync mkdocs build --strict
openspec validate --all --strict
VERSION=$("$UV" run --no-sync python -c 'from importlib.metadata import version; print(version("iddqueue"))')
BUILD_DIR="dist/$VERSION"
"$UV" build --out-dir "$BUILD_DIR"
"$PYTHON" scripts/check_license.py "$BUILD_DIR/iddqueue-$VERSION-py3-none-any.whl" "$BUILD_DIR/iddqueue-$VERSION.tar.gz"
"$PYTHON" scripts/check_package.py --quickstart --expected-version "$VERSION" "$BUILD_DIR/iddqueue-$VERSION-py3-none-any.whl"
export IDDQUEUE_BUILD_DIR="$BUILD_DIR"
"$PYTHON" - <<'PY'
import hashlib
import os
import subprocess
from pathlib import Path
print("Checked commit:", subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip())
print("Working tree:", subprocess.check_output(["git", "status", "--short"], text=True).strip() or "clean")
for path in sorted(Path(os.environ["IDDQUEUE_BUILD_DIR"]).glob("iddqueue-*")):
    print("SHA256:", hashlib.sha256(path.read_bytes()).hexdigest(), path)
PY
