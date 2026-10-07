# IDDQueue 0.13.0rc4

Fourth release candidate, following [RC3](rc-0.13.0rc3.md).

## Changes since RC3

- Queue/domain snapshots and optional Prometheus domain gauges.
- Optional synchronous SQLAlchemy Connection/Session transactional publication with Psycopg 3; business changes and tasks commit or roll back together.
- Debugging guide, separate storage exporter example and Grafana dashboard, including dotted/multiple domains.
- External schema management, custom recipes and native graceful SIGHUP/SIGTERM worker lifecycle guidance.
- Malformed NOTIFY hints are discarded without tearing down consumers. Claims still use durable database contents; UUID lock identity is consistent for claim/ACK.
- Claim SQL acquires its session advisory lock once per statement even with sequential scans, so one ACK/NACK releases it.
- Local PostgreSQL Compose binds to loopback. Deterministic retry/delay/crash regressions and hard-restart metrics directory guidance.

No DDL migration is required from RC3. SQLAlchemy/monitoring extras remain
optional; broker/workers use synchronous Psycopg 3. Delivery remains at least
once. Actors must be idempotent; crash/restart can repeat side effects.
When using custom noncanonical UUID message IDs, stop old workers before
upgrading to avoid mixing advisory-lock identity conventions. Standard
Dramatiq-generated UUID lock keys are unchanged.

## Install

```sh
uv pip install "iddqueue[binary]==0.13.0rc4"
# Optional producer adapter and monitoring:
uv pip install "iddqueue[binary,sqlalchemy,monitoring]==0.13.0rc4"
```

Security review covered all production Python/SQL, executable tests/examples,
scripts and CI at commit 28044df. Two findings (medium notification DoS and low
local example network binding) were addressed before this candidate. Historical
prose and dependency vulnerability feeds were not comprehensively audited;
this is not a guarantee that the project has no vulnerabilities.

See [debugging](debugging.md), [SQLAlchemy](sqlalchemy.md), [domains](domains.md),
[deployment](deployment-guide.md) and [release checks](release.md).
PostgreSQL license and original contributor credits are preserved.
