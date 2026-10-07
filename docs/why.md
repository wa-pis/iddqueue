# Why PostgreSQL

IDDQueue stores Dramatiq tasks and results in PostgreSQL. If an application already operates PostgreSQL, this can avoid a separate broker service while supporting transactional publication alongside business writes.

## How it works

Messages are durable JSONB rows. LISTEN/NOTIFY wakes consumers; notifications contain IDs, not task payloads. Consumers read authoritative rows and claim work using session advisory locks. Startup and idle scans recover work when wakeups are missed. PostgreSQL notifications themselves are not durable task storage.

Tasks and results share the queue table; coordination, deduplication, queue control, attempt history and schedules have separate tables. Optional features can add SQL operations. Result storage and retention also affect the workload. See the [user guide](user-guide.md) for behavior and limits.

## Trade-offs

Database CPU, connections, WAL, indexes, autovacuum and storage are shared with other application workloads. Size pools across all producer/worker processes, retain sessions for LISTEN/NOTIFY and advisory locks, and measure interference with business queries. A separate broker can be appropriate when operational isolation or workload characteristics require it.

Delivery remains at least once; database persistence does not provide exactly-once actor side effects. Actors must be idempotent. Failover/session loss can lead to recovery and repeated execution. PgBouncer transaction pooling is unsuitable for the session-bound consumer design.

RC4 transactional enqueue uses the caller's synchronous Psycopg connection; it makes the task and business writes visible together on commit. Publishing from an independent pool is not atomic with a separate application transaction. See [deployment guidance](deployment-guide.md).

## Performance evidence

No current IDDQueue throughput or latency advantage over other brokers has been established. Historical dramatiq-pg laptop figures are not benchmarks of this Psycopg 3 implementation. Measure your own payload sizes, actor duration, concurrency, database topology and retention policy before sizing deployment.

The inherited [perf.py](https://github.com/wa-pis/iddqueue/blob/main/tests/perf.py) and [perfagg.py](https://github.com/wa-pis/iddqueue/blob/main/tests/perfagg.py) scripts are exploratory tools, outside the current acceptance suite. They are not a validated performance guarantee or a required development check; review their setup before running them on a separate test database.

The development branch also provides explicit awaitable transactional publication on Psycopg AsyncConnection; it is not included in RC4. See [async recipes](recipes.md#async-transactional-publishing-development).
