# Evidence — 2026-10-07

## Scope

Проверен development checkout 0d03883, без runtime edits, публикации или изменения исходных RC3 assets. Проверка ограничена ~2 минутами; throughput benchmark и длительный leak test не заявляются.

## Timing tests

- Первый запуск retry/delay/retry-lock-release: 3 passed 7.44s. Затем пять отдельных запусков: все 3 passed (8.49/7.49/7.44/7.42/7.46s).
- Listener.wait воспроизводимо принимает NOTIFY с message_id unrelated-task, не проверяя связь с отправленной задачей. Старый test_delay измеряет любые первые два ACK, включая незавершённые retries предыдущего теста.
- failing(always=False) принимает random.randint, поэтому успех не ограничен budget теста. Seed 71729 даёт 16 единиц в отдельном Random; это иллюстрация случайности, не гарантия тех же worker decisions (worker также расходует RNG).
- SEED=71729 retry+delay: 2 passed, 1 teardown error Timeout>8s, 10.29s. Не объявлено исправленным или доказанным runtime defect. Test timeout захватывает teardown и способен оборвать worker cleanup.
- Старый test_retry_wakes_consumer_after_old_lock_release ожидает message после одного next с timeout20ms. Во время этих запусков passed; previous CI None не воспроизведён.

## Installed wheel and soak

- Сборка /tmp/iddqueue-readiness-build, отдельный clean venv /tmp/iddqueue-readiness-venv, binary+monitoring+sqlalchemy. Application вне checkout; assertion iddqueue.__file__ в venv passed.
- Development metadata всё ещё 0.13.0rc3; это локальный development wheel, НЕ опубликованный RC3. Wheel SHA256 6a202b456597df20e2aef1eddbaa4b70cd002462edbee056adb2ee9aedbb43e1, sdist 893d5b2bb6afdc451a9fd478c47267f6c3d7ca08561fb9c3859498efb1a002a2.
- Dedicated PostgreSQL14.20, schema readiness_probe. SQLAlchemy Connection бизнес-запись+Domain enqueue commit/result passed; rollback бизнес-запись+task absent passed. Shipping.eu echo result passed.
- Две replicas по два spawned processes, четыре threads/process. 2340 задач billing, 120.66s, 117 domain snapshots. Каждый десятый key имеет deterministic first-attempt failure, max_retries1/backoff50ms. Через35s SIGKILL целой первой process group, затем restart двух processes.
- Все 2340 результатов равны исходным keys. 2578 actual actor entries, max3 per key: retry плюс повторная доставка после crash. Это at-least-once, не exactly-once. Второй домен: два успешных echo. Итог queue: done2342, queued/consumed/rejected absent.
- Idle connection sample49 для application_name readiness (producer+worker pools), после shutdown/engine.dispose/broker.close:0. Не измерялся peak всей нагрузки; отсутствие роста не доказано двумя точками.
- queue total relation size1368064 bytes, retained2342 rows. Explicit namespace PURGE with max_age0 seconds удалил2342 rows, осталось0. Это ручная очистка disposable data, не automatic retention. Relation size послеDELETE не обещает shrink.
- Initial harness errors исправлены: table attempts совпало с generated history table, переименовано probe_attempts; worker cwd неверный -> application directory. Эти errors не относятся к пакету. uv cache broken archive -> no-cache install passed.

## Grafana

- Official Grafana13.2.3 commit90ffed056f0884267356c12a0eeb72a022af53f1, Prometheus3.15.0, Colima containerd. Disposable containers удалены, Colima остановлен; PG schema dropped, PG остановлен.
- API dashboard import original dashboard.json status success; all12 panels rendered, storage/native metrics реальные (scrape every5s, all3 targets up). Billing panels include retries/rate/p50/p95/error actor, terminal rejects No data (не генерировались).
- Domain selector содержит billing/empty/shipping.eu. Empty: storage gauges0, native processing No data без подмены0.
- Shipping.eu selection FAIL: unknown escape sequence U+002E '.' в Prometheus query. Current ${domain:regex} interpolation даёт один backslash внутри PromQL string; previous manual promtool substitution не моделировала Grafana interpolation.
- После SIGKILL и reuse одного replica dramatiq_prom_db: native dramatiq_messages_inprogress остаётся5 при отсутствии задач. Dramatiq uses livesum, mark_process_dead only graceful worker_shutdown. Операционное ограничение native middleware, требуется корректная инструкция lifetime/cleanup, не собственный processing counter.
- Initial datasource URL host.lima.internal:9095 недоступен из Grafana container, заменён на Prometheus container10.4.0.13:9090. Это ошибка stand wiring; queries после исправления выполняются.
- Screenshots locally /tmp/readiness-grafana-dotted-error.png, /tmp/readiness-grafana-empty.png, /tmp/readiness-grafana-billing.png.

## Findings

Follow-up change fix-readiness-observation-gaps: dashboard interpolation, deterministic/message-specific timing tests, native Prometheus hard-restart lifecycle guidance. Эта проверка не исправляла findings и не заявляет readiness next RC.

Local full suite:175passed57.96s; Ruff passed; uv lock --check passed; build/LICENSE passed. No runtime changes. Remote CI pending.
