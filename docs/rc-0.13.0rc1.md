# IDDQueue 0.13.0rc1

First release candidate for the independent IDDQueue fork of
[DALIBO dramatiq-pg](https://gitlab.com/dalibo/dramatiq-pg).
This is a prerelease for evaluation, not a published stable release.
The PostgreSQL [license](https://github.com/wa-pis/iddqueue/blob/main/LICENSE) and original contributor credits are preserved.

## Included

Synchronous Psycopg 3 and Dramatiq 2.2.1+, transactional/batch enqueue,
PostgreSQL coordination, deduplication, queue control/cancellation, failure retry,
attempt history, scheduling, namespace isolation, optional Prometheus metrics,
and a [FastAPI example](fastapi.md). See the [changelog](https://github.com/wa-pis/iddqueue/blob/main/CHANGELOG.md).
Task notifications carry message IDs only; consumers retrieve authoritative SQL rows.

## Test installation

From the verified checkout, artifacts are built into `dist/0.13.0rc1/`:

```sh
uv pip install 'dist/0.13.0rc1/iddqueue-0.13.0rc1-py3-none-any.whl[binary]'
iddqueue --version
```

The expected CLI/metadata version is `0.13.0rc1`. Monitoring is optional; use
`[binary,monitoring]` when needed. FastAPI is an example dependency group, not
part of the package runtime. Published on [PyPI](https://pypi.org/project/iddqueue/0.13.0rc1/) and
[GitHub](https://github.com/wa-pis/iddqueue/releases/tag/v0.13.0rc1/).
Install from PyPI with `uv pip install "iddqueue[binary]==0.13.0rc1"`.
The repository is public.

## Migration and limits

Follow the [migration guide](migration.md): stop all participants, back up data,
update imports/CLI/metric names, run `iddqueue upgrade`, then restart participants
with consistent schema/prefix and feature flags. Update every publisher, worker
and scheduler to remove older payload-bearing notifications. Do not run `init`
over existing storage. Non-default namespaces change channels/lock domains.

Delivery is at least once: tasks and callbacks must be idempotent. Cancellation
of running work is cooperative. Scheduling uses fixed intervals. Async actors
use Dramatiq middleware; publication/results remain synchronous. FastAPI async
endpoints offload publication to a thread; AsyncConnection transactional enqueue
is unsupported. Disconnecting an HTTP client does not cancel a commit.

A downgrade is not a reverse schema migration. Preserve the backup and previous
application configuration; follow the migration guide's rollback limitations.

## Candidate evidence

The OpenSpec `prepare-rc-release` evidence records the candidate SHA, actual CI,
commands, wheel/sdist SHA256 and known limitations. Build hashes identify those
specific artifacts. [Release procedure](release.md) covers repeatable validation.
GitHub prerelease and PyPI publication completed; TestPyPI was not used.
