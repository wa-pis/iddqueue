# Evidence

2026-10-07: Domain reuses native Dramatiq Actor and a private declaration Broker with no middleware/transport. Explicit startup register checks options/collisions first, idempotent same-broker registration, forbids rebind/new declarations; hook failures return imported handles to declaration broker, rejecting enqueue.

9 unit tests cover no default broker lookup, stable Actor identity, native callback names, direct calls/messages, deferred options validation, delay/timedelta, lifecycle/isolation, domain name/collision validation, failure guard and native async adaptation. Two PostgreSQL tests use a separate standard CLI worker with four spawned processes, two domain queues, Results and executed pipelines/groups; queue-filtered worker leaves the other domain queued. Producer passes explicit libpq connstring at startup, worker reads runtime settings.

Final local release gate: 158 tests passed in 53.04s, Python 3.13.14 / dedicated PostgreSQL 14.20 port 55433. Ruff, uv lock --check, source docs, strict MkDocs/OpenSpec, wheel/sdist LICENSE, clean base/monitoring installed wheel Domain smoke acceptance and installed quickstart result=5 passed.

Initial probes exposed missing declaration declare_queue implementation and functional conftest package import; corrected before final checks. Previous temporary cluster directory disappeared; fresh isolated /tmp/iddqueue-domains-pg initialized, no application database used.

Docker application example supplied but not executed: docker info failed because /var/run/docker.sock daemon is unavailable. No container execution or multi-container replicas claimed. Standard spawned CLI and queue filter commands executed.

Experimental gate wheel/sdist SHA256: 6b30a07a64b5bcc5919bf59dcac6b8f04678ad3708df9c94acefc63fea8c6faa / d8c6141276678dff972a27b5af193efb0af68d069440f4ab68f2a78112ecbbad. No publication/version bump; original published RC2 local assets preserved separately and restored after checks. Actual CI pending.

CI первого commit 211dfe3: run 37531316719 выявил Python 3.10 mock target resolution (dramatiq.actor разрешался как функция). Тест исправлен через явный import_module + patch.object; production API не затронут. Documentation 37531316726 success.
