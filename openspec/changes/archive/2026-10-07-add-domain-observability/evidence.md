# Evidence

2026-10-07: 7 focused tests passed; full suite 165 passed in 57.06s on dedicated PostgreSQL 14.20 port 55433/Python 3.13.14. SQL filtered single snapshot aggregates DQ/main, empty/dotted names and isolated namespace; future prefetch, cancelled/done/rejected/retention checked. Domain and queue collectors coexist; registration no I/O. Native processing metrics test verifies actual queue_name labels with executed actors/retries. Ruff/lock/docs/strict MkDocs/OpenSpec, build/LICENSE and clean base/monitoring installed wheel smoke passed. Development builds /tmp/iddqueue-domain-metrics-build; published RC3 assets untouched. CI pending.

Signed implementation 6e65d5e; actual Tests 37540304330 success 6/6, Documentation 37540304436 success. Main spec synced, archived 2026-10-07.
