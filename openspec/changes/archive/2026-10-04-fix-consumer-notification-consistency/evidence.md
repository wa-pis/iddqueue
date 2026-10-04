# Evidence — 2026-10-04

Dedicated PostgreSQL 14.20, Python 3.13.14. Regression-before:
7 failed / 3 passed in 0.31s. Regression-after: 10 passed in 0.24s.
Full suite: **130 passed in 50.00s**. Ruff, poetry check, strict OpenSpec
и git diff --check прошли. Packaging/SQL resources не изменены.

Проверены stale actor/kwargs/retry options, normal→DQ с ETA, deleted large
message, done/rejected/cancelled hints, ACK/NACK backlog и prefetch saturation,
competing session lock acquisition. Existing full suite покрывает namespace,
large payload, disconnect/recovery, cancellation/pause, fast retry и middleware.
Test instrumentation переключена с fetch_by_id на authoritative consume_one
результат; логические проверки namespace/prefetch сохранены.

CONSUME_ONE фильтрует queue и RETURNING message; consumer читает hint JSON
один раз, payload notification не исполняет. Удалены неиспользуемые FETCH_BY_ID
SQL/helper; unlock drain перенесён перед prefetch guard. Wire formats сохранены,
новых dependencies/migrations нет. Отдельная fetch_by_id ветка убрана,
контракты/проверки сохранены.

Commit 3c9b459 отправлен в main. Все шесть jobs CI прошли:
https://github.com/wa-pis/iddqueue/actions/runs/37192114318.
Spec синхронизирован; change архивирован 2026-10-04. Checks после archive
записаны в итоговом выводе; следующая работа — maintenance practices.
