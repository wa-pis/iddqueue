# Проверки — 2026-10-07

Исходная shipping.eu regression подтверждена в verify-engineering-readiness screenshot/parse error. Dashboard использует native Prometheus `${domain}` вместо `${domain:regex}`. В реальной Grafana13.2.3 импортирован новый dashboard; UI shipping.eu, billing+shipping.eu, All отображает все12панелей без parse errors, storage series соответствуют выбору (All включает empty). No data допустим для отсутствующих native counters; не заменяется fictitiouszero. Screenshots /tmp/rc4-grafana-{shipping,multi,all}.png. Дополнительно36expanded PromQL queries accepted Prometheus3.15.0; ручной escaping не считается native interpolation evidence.

Installed development-wheel runtime stand:160billingtasks8.59s, SIGKILL whole two-process replica/restart со fresh mkdtemp directory, allresults, SQLAlchemy commit/rollback и shipping.eu echo passed. Actor entries180/max2; at-least-once. Оба native endpoints9193/9194 idle inprogress0, все три Prometheus targetsup. Это короткая restart regression, не замена прежнего120.66s soak; wheelversionrc3 development build, не publishedrc3.

Tests теперь deterministic retry marker/pg_failure, message-specific execution timestamps/ETA и bounded observer deadline2s после locks. Full188passed61.47s на dedicatedPG. Repeat checks ещё ожидаются. Ruff/lock/strictdocs passed; OpenSpec/remoteCI/архив pending.

Пять отдельных последовательных повторов retry/delay/lock-release: каждый3passed,9.48/9.53/9.50/9.49/9.47s. Stand завершён SIGTERM, CONNECTIONS_AFTER_CLOSE0, temporaryschema удалена. Full188passed61.47s; strict OpenSpec22/22passed. CI ещё pending.
