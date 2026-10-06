## Context

Последний docs CI 37543145122 первоначально failed retry timeout8s/delay0.018636s, rerun passed. Retry actor случайный; ACK listener не фильтрует message ID. SQLAlchemy и domain metrics реализованы после RC3. Grafana ранее проверен лишь promtool.

## Goals / Non-Goals

Проверить четыре согласованных риска фактическим запуском. Не обещать production throughput или exactly-once, не публиковать RC.

## Decisions

Переиспользовать существующие func tests и Docker/Colima; build вне dist релизов. Installed acceptance с временным schema и чистым venv, совместным SQLAlchemy/monitoring extras. Dashboard import в локальный disposable Grafana и UI inspection. Ограниченный soak около двух минут с отдельными worker processes, повторяемыми retry и рестартом; наблюдать rows/connections.

## Risks / Trade-offs

Один повтор не доказывает отсутствие flaky tests. Случайный retry и неидентифицированные ACK могут давать ложные failures; findings записывать отдельно от runtime дефектов. Ограниченный soak не заменяет длительную production нагрузку.
