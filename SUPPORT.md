# Compatibility and support

IDDQueue is pre-1.0. The tested baseline is Python **3.10, 3.13, 3.14** on
PostgreSQL **14 and 18** (six CI combinations). Python 3.11/3.12 and other
PostgreSQL releases are not covered by this matrix; broad dependency ranges
are installation constraints, not evidence of compatibility with every version.
Current ranges: Python >=3.10,<4; Dramatiq >=2.2.1,<3; Psycopg >=3.3.6,<4;
psycopg-pool >=3.3.3,<4; Tenacity >=9,<10. Use synchronous Psycopg 3 pools.
Base installs require libpq; binary and monitoring are optional extras.

Documented supported surfaces: PostgresBroker, PostgresBackend,
PostgresRateLimiterBackend, ResultCancelled, schema SQL generators exported
by iddqueue; transactional enqueue, result storage, namespaces and standard
Dramatiq middleware/composition. The newer deduplication/batch, queue controls,
cancellation, attempt history and fixed interval scheduler APIs are experimental
pre-1.0 extensions. They are tested, but may change with documented migration.
Private helpers, query templates and direct table mutation are implementation
details. See [API](docs/api.rst) and [limitations](docs/user-guide.rst).

Documented CLI commands and JSON fields are integration surfaces. Use global
storage flags before commands. UUID pagination is not chronological ordering;
missing objects return documented missing states/nonzero exit codes. Consumers
should tolerate additional JSON fields; removed/renamed fields, changed types
or semantics require release notes and migration guidance. Help text/log wording
is not a machine-readable contract. Raw SQL layouts are managed by init/upgrade;
custom queries must be reviewed against the installed schema version.

No blanket 1.x semantic-versioning guarantee is made. Breaking changes to
Python requirements, supported API/CLI/JSON or storage must be explicit in
[CHANGELOG](CHANGELOG.md), with migration steps and updated tests/docs. Stop
participants for SQL or namespace migrations, back up data and upgrade every
producer/worker/result reader/scheduler together. Code rollback does not undo
DDL; use a compatible backup or a planned reverse migration.

Delivery remains at least once. Deduplication is publication suppression;
cancellation of started actors is cooperative; history is diagnostic;
scheduler coalesces missed fixed intervals. These limits are part of the API.

Report reproducible issues via [GitHub](https://github.com/wa-pis/iddqueue/issues)
(repository access required), including versions, namespace/configuration,
expected/actual behavior and sanitized reproduction. Maintainer support has no
response-time SLA. Upstream integrations need separate compatibility validation.
