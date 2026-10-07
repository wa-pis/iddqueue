# IDDQueue 0.13.0rc5

RC5 adds async transactional publication to RC4. This is a prerelease for evaluation.

## New API

- `await broker.enqueue_in_transaction_async(message, connection=connection, ...)`
- `await broker.enqueue_many_in_transaction_async(messages, connection=connection, options=options)`

Use a caller-owned active Psycopg 3 AsyncConnection in the same database as the
business writes. Delay/deduplication and ordered batches up to 1000 inputs are
supported. Batch/deduplication operations use savepoints; errors and cancellation
propagate without internal retries, outer commit or connection close.

Enqueue hooks remain synchronous and pre-commit. Ordinary actor.send, consumers,
results and optional SQLAlchemy adapter remain synchronous. See the
[async recipe](recipes.md#async-transactional-publishing) and [API](api.md).

## Upgrade

No DDL migration from RC4. Existing sync calls remain compatible; RC1–RC4 artifacts
are immutable. Tasks still require idempotency for at-least-once delivery.

```bash
uv pip install "iddqueue[binary]==0.13.0rc5"
```

## Verification

Local release gate: 200 tests passed, async actor recipe, strict docs/OpenSpec,
build/LICENSE and isolated installed-package checks passed. Six candidate
Python/PostgreSQL CI jobs must pass before publication.
Static Codex Security diff review of e56c6b1..414e1c6 covered20changed paths and
found no new security findings; production grants/dependency advisory feeds were
not audited. See [changelog](https://github.com/wa-pis/iddqueue/blob/main/CHANGELOG.md).
