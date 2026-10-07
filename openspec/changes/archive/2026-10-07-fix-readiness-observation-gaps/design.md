## Context

Readiness verification воспроизвёл dotted shipping.eu -> PromQL unknown escape sequence. ${domain:regex} manually tested с дополнительным escaping, которое реальная Grafana не делает. ACK listener accepts unrelated message ID; retry actor random. Dramatiq native livesum очищает PID files в worker_shutdown, SIGKILL skips hook.

## Goals / Non-Goals

Исправить проверяемость и example correctness без изменения PostgreSQL broker. Не переписывать Prometheus middleware, не увеличивать timeout как единственное исправление.

## Decisions

Для Prometheus variable использовать native datasource interpolation (проверить ${domain} без custom :regex в реальной Grafana) и retainescaped literal .DQ. Regression acceptance dotted/multi/All. Retry deterministic actor использует существующий PG witness marker, deadline и конкретный result/task ID. Delay измеряет actor execution/result timestamp и ETA, не notification order. Для test20ms повторять наблюдение в ограниченном deadline, сохраняя initial lock-contention assertion. Fresh multiprocess directory для каждого replica lifetime; не очищать active replica directory, объяснить counter resets/no-data при restart.

## Risks / Trade-offs

Crash after side effect может повторить delivery: это контракт. Directory reset теряет process-local metrics и сбрасывает counters; запись guidance должна учитывать scrape/rate resets, не обещать точность в crash window. User ask был verification; этот change лишь план, apply pending.
