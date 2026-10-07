## Context

pg_try_advisory_lock(%s) в per-row WHERE reenters session lock до UUID/queue filters. Seq Scan plan(PG18.6) на50unrelatedrows:51acquisitions, один ACK unlock оставляет50. Аналогичный план допустим на PG14. Предыдущие6/6 CI проходы не гарантируют иной план на будущих данных.

## Decisions

Использовать AND (SELECT pg_try_advisory_lock(%s)): uncorrelated scalar InitPlan выполняется один раз на SQL statement, без row dependency. Сохранить параметры, durable filters и release при неуспешном claim. Не использовать repeated unlock loop, не отключать Seq Scan в production и не увеличивать timeout ради masking.

## Risks / Trade-offs

Statement может взять lock до проверки missing/terminal row, existing consume_one release возвращает его. Claims одной задачи всё ещё serialized session advisory lock; at-least-once сохраняется. Проверить missing/terminal hints, repeat notifications и retry wakeups. PostgreSQL documentation: https://www.postgresql.org/docs/18/explicit-locking.html#ADVISORY-LOCKS .
