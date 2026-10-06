# Evidence

Installed development wheel из readiness verification, Python3.13.14/Dramatiq2.2.1/PG14.20, dedicated schema readiness_probe. Native CLI два spawned worker processes × два threads.

- SIGHUP при active3s actors: все8results obtained. Initial PIDs95948/95949; completion across old/new95972/95973; next task ran95972. Pending prefetched messages пережили reload.
- SIGTERM после SQL witness начала следующего3s actor: result obtained, exit0, shutdown5.0s. Total10unique keys, sumattempts10/max1; это наблюдение данного graceful run, не exactly-once promise.
- После broker.close и worker exit: application database sessions0, disposable schema dropped.
- First harness неверно сравнил PID нового actor со всеми completion PIDs, включая задачи, выполненные послеreload; assertion исправлен на initial ready PIDs. Это ошибка harness, не runtime.
- Docs links, MkDocs strict, OpenSpec strict passed. Native flags/default прочитаны из установленного Dramatiq cli: default worker shutdown timeout600000ms.
- Docker commands документированы; текущая проверка signals native macOS CLI, Docker-specific grace commands в этом этапе не запускались. Предыдущий Dockerfile acceptance прошёл отдельным change.

Local full suite:175passed57.96s; Ruff passed; uv lock --check passed; build/LICENSE passed. No runtime changes. Remote CI pending.

Remote Tests37547185094:6/6 first-attempt success on signed718927461280fd4dd57bea582a76a609d5295410 (includes prior signed verificationbcaaacc46858062f85af03ed376edfd53b06c277). Documentation37547185152success/deployed. Verification-only parent run cancelled by superseding main push, not counted as completed check. Findings remain planned, not fixed.
