# Contributing

Use OpenSpec for proposed behavior: read [AGENTS](AGENTS.md),
[roadmap](openspec/roadmap.md) and relevant specs/change artifacts first.
Keep each change small; reuse existing SQL/helpers and synchronous Psycopg 3.
Preserve [LICENSE](LICENSE) and contributor attribution.

Install development tools with `poetry install --extras "binary monitoring"`.
Functional tests terminate PostgreSQL connections and crash workers: configure
PGHOST/PGPORT/PGUSER/PGPASSWORD/PGDATABASE for a dedicated instance.
Prepare a fresh test database:

```sh
poetry run iddqueue init
poetry run python tests/pypsql < tests/func/schema.sql
export IDDQUEUE_TEST_DATABASE=dedicated
poetry run sh scripts/check_release.sh
```

Preparation is for fresh storage; do not rerun CREATE SCHEMA functest over an
existing schema. The release command includes Ruff, unit/functional tests,
strict docs/local links, OpenSpec, build/LICENSE and isolated wheel/quickstart.
It needs libpq, Poetry, OpenSpec 1.12.0 and package-index access for clean installs.
Individual checks and release evidence: [guide](docs/release.md).

For bugs, reproduce first, add a meaningful regression check, then implement.
For public behavior, update API/operations docs, migration guidance and
[CHANGELOG](CHANGELOG.md). Keep internal bookkeeping out of user release notes.
Update task boxes only after checks run; distinguish local results from GitHub CI.

A PR should explain the problem/result, list actual checks, note compatibility
or migration effects, and link its OpenSpec change. A bug report needs a minimal
sanitized reproduction, expected/actual behavior and versions; a feature request
needs a concrete use case and limits.
Commit completed features separately; verify the six CI jobs before completion.
Package upload and release tags require a separate explicit request.
