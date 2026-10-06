# IDDQueue 0.13.0rc2

Second release candidate, following [RC1](rc-0.13.0rc1.md).

## Changes since RC1

- Published searchable documentation with manual steps and CLI commands.
- Refreshed installation, migration, API and upstream comparison guides.
- Removed obsolete legacy assets/configuration and local agent skills from Git.
- Moved functional worker actors into tests and optional PostgreSQL Compose into examples.
- Removed unused Dramatiq watch extra and redundant CLI parser defaults.

Runtime APIs, database schema and delivery guarantees are unchanged. Existing
RC1 installations can update the package without a new schema migration.
Delivery remains at least once; actors must be idempotent.

## Install

```sh
uv pip install "iddqueue[binary]==0.13.0rc2"
```

See [walkthrough](walkthrough.md), [migration](migration.md),
[FastAPI](fastapi.md) and [release checks](release.md). This is a prerelease
for evaluation. The PostgreSQL license and original credits are preserved.
