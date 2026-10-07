## Why

Engineering verification выявил parse error dashboard для dotted domain, ненадёжные ACK/random-based tests и stale native inprogress после hard restart.

## What Changes

- Исправить Grafana variable interpolation без двойного escaping, проверить реальные shipping.eu и multiple/All values.
- Заменить random retry test на controlled failure/release и измерять completion по message ID; ограничивать ожидание общим deadline, не считать первый idle next доказательством missing retry.
- Документировать worker replica lifetime Prometheus directories и hard-crash cleanup только после остановки всех использующих directory processes; повторить restart acceptance.

## Capabilities

### New Capabilities
Нет.

### Modified Capabilities
Нет: исправление existing examples/tests/documentation contracts, skip_specs: true.

## Impact

examples/monitoring/dashboard.json, tests и docs/debugging.md. Без broker counters/schema/новых dependencies. Implementation не выполнена; findings из verify-engineering-readiness.
