# Evidence

2026-10-07: two focused tests passed; full suite 160 passed in 53.27s on dedicated PostgreSQL 14.20 port 55433/Python 3.13.14. External generated SQL creates isolated schema; role with USAGE/data permissions but no schema CREATE performs enqueue/consume/Results/ack. Missing schema raises UndefinedTable and remains absent. Ruff/uv lock/docs/strict MkDocs/OpenSpec passed. Runtime/package unchanged. CI pending.

Actual Tests 37539694974 success 6/6, Documentation 37539694960 success; signed implementation 3f3594b7169af4c238a1ae2805975e1d20f2c6f5. Main spec synced, archive 2026-10-07.
