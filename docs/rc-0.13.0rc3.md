# IDDQueue 0.13.0rc3

Third release candidate, following [RC2](rc-0.13.0rc2.md).

## Changes since RC2

- Add `Domain(name)` with domain-derived queues and qualified actor names.
- Declare/import native Dramatiq actors before DSN or broker initialization; register once at process startup. Sending before registration raises a clear error.
- Framework-independent multi-domain bootstrap and standard spawned worker/container example.
- Verify Results, pipelines/groups, queue filters, multi-container replicas and graceful shutdown. Document pool connection budgets.

The API is additive and opt-in. Existing `dramatiq.actor` applications need no
change. No new database schema migration or dependency is required. Delivery
remains at least once; actors must be idempotent. `Domain` is not hot rebinding
or database access isolation. Every producer/worker process needs startup
registration.

## Install

```sh
uv pip install "iddqueue[binary]==0.13.0rc3"
```

See [Domain guide](domains.md), [walkthrough](walkthrough.md),
[migration](migration.md) and [release checks](release.md). This prerelease is
for evaluation. PostgreSQL license and original contributor credits preserved.
