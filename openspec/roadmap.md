# План развития PostgreSQL-проекта

## Tooling — 2026-10-04

[migrate-to-uv](changes/archive/2026-10-04-migrate-to-uv/proposal.md): выполнен переход Poetry → uv, lock/dev groups/build/CI/release gate/docs. Версии зависимостей сохранены; 143 tests passed, installed wheel/quickstart/LICENSE passed, CI 37228008729 6/6 success. Main spec synced; change архивирован. Runtime и публикация вне scope.

## Security remediation — 2026-10-04

[fix-notification-payload-disclosure](changes/archive/2026-10-04-fix-notification-payload-disclosure/proposal.md): medium CWE-200 исправлен: ID-only ENQUEUE/ACK/NACK, restricted-role regression, migration guidance. 143 tests passed, CI 37225306000 6/6 success, main spec synced; change архивирован. Публикация вне scope.

## Документация перехода — 2026-10-04

[document-upstream-comparison](changes/archive/2026-10-04-document-upstream-comparison/proposal.md): выполнено: ссылка upstream, таблица различий и инструкция migration/rollback. Upstream fixtures upgrade/backup restore проверены; 131 tests passed; CI 37224331994 6/6 success. Change архивирован; runtime и публикация вне scope.

Транзакционная отправка реализована и архивирована 2026-10-02 (38 тестов прошли). Координация PostgreSQL реализована и архивирована 2026-10-02 (45 тестов прошли). Совместимость middleware и композиции Dramatiq проверена и архивирована 2026-10-02 (51 тест прошёл). Диагностика ошибок и выборочный retry реализованы и архивированы 2026-10-02 (56 тестов прошли). Метрики очереди реализованы и архивированы 2026-10-02 (58 тестов прошли). Изоляция namespace реализована и архивирована 2026-10-02 (63 теста прошли). Все шесть запланированных локальных фич завершены; GitHub setup завершён: wa-pis/iddqueue, private, main; все шесть jobs run 37057164073 прошли. Выполненная миграция и оставшиеся шаги GitHub отражены отдельно в `modernize-postgres-broker`.

| Порядок | Change | Результат | Зависимость |
| --- | --- | --- | --- |
| 0 | [modernize-postgres-broker](changes/archive/2026-10-02-modernize-postgres-broker/tasks.md) | Psycopg 3, Dramatiq 2.2.1, новый GitHub-проект и CI | Базовая работа |
| 1 | [transactional-enqueue](changes/archive/2026-10-02-transactional-enqueue/proposal.md) | Выполнено: бизнес-данные и задача в одной транзакции | Runtime миграции |
| 2 | [postgres-coordination](changes/archive/2026-10-02-postgres-coordination/proposal.md) | Выполнено: лимиты, барьеры и group completion callbacks без Redis | Runtime миграции |
| 3 | [dramatiq-feature-compatibility](changes/archive/2026-10-02-dramatiq-feature-compatibility/proposal.md) | Выполнено: pipelines, groups, async actors, retry exhaustion callback, timedelta | Runtime; group callbacks после coordination |
| 4 | [failed-task-management](changes/archive/2026-10-02-failed-task-management/proposal.md) | Выполнено: ошибки, диагностика и выборочный retry | Runtime миграции |
| 5 | [postgres-queue-metrics](changes/archive/2026-10-02-postgres-queue-metrics/proposal.md) | Выполнено: backlog и возраст задач, опциональный Prometheus | Runtime; согласовать metadata с failed-task-management |
| 6 | [result-namespace-isolation](changes/archive/2026-10-02-result-namespace-isolation/proposal.md) | Выполнено: изоляция схем/префиксов, уведомлений, locks и результатов | Runtime; область хранения переиспользуется coordination/metrics |

Порядок рекомендованный: первый этап — транзакционная отправка и backend координации. Изоляцию namespace желательно включить до многопользовательского использования и согласовать до стабилизации схемы coordination. Возможности middleware проверяются через стандартные реализации Dramatiq, без собственного orchestration engine. Actor priority документируется как локальный порядок prefetched-сообщений worker; глобальный планировщик приоритетов не включён.

Пользователь выбрал IDDQueue: репозиторий, distribution/import/CLI — iddqueue. GitHub: wa-pis/iddqueue, private; удалённая матрица прошла. Публикация в PyPI не входит в этот план без отдельного запроса.

CLI init/stats/purge/recover/flush на нестандартных schema/prefix проверены 2026-10-02: 64 теста прошли. Все независимые локальные задачи baseline завершены; задачи 5.1–5.5 завершены; baseline синхронизирован и архивирован.

## Сохранение лицензии форка

[preserve-fork-license](changes/archive/2026-10-02-preserve-fork-license/proposal.md) — выполнено: сохранение полного LICENSE/copyright DALIBO в исходниках и wheel/sdist, README attribution и проверка упаковки в CI. LICENSE и метаданные в wheel/sdist проверены; отрицательные проверки успешны. Публикация не выполнена. Этот этап независим от решения об имени GitHub-проекта.

CI-регрессии retry wakeup и изоляции recover test исправлены; локально 65 tests passed.
Предыдущие changes завершены и архивированы. Публикация пакета требует отдельного запроса.


## Следующая очередь работ — 2026-10-03

[extend-postgres-capabilities](changes/archive/2026-10-03-extend-postgres-capabilities/proposal.md) —
этап 1 завершён (80 tests passed, все шесть CI jobs run 37063065568 success); этап 2 завершён (87 tests passed, шесть CI jobs run 37065548460 success); этап 3 завершён (97 tests passed, шесть CI jobs run 37069326903 success); этап 4 завершён (102 tests passed, шесть CI jobs run 37070389403 success); этап 5 завершён (105 tests passed, шесть CI jobs run 37071887095 success); этап 6 завершён (113 tests passed, шесть CI jobs run 37072742814 success); этап 7 завершён (120 tests passed, шесть CI jobs run 37073608454 success). Proposal, design, семь delta specs и
[tasks](changes/archive/2026-10-03-extend-postgres-capabilities/tasks.md) описывают этапы.
Каждая фича выполняется последовательно и фиксируется отдельным commit.

| Этап | Возможность | Зависимость |
| --- | --- | --- |
| 1 | Дедупликация отправки: ключ, TTL, конкурентные producers | Transactional enqueue |
| 2 | Pause/resume очереди, включая DQ и prefetched tasks | Control table/migration |
| 3 | Отмена до старта и cooperative cancellation | Pause/start gate |
| 4 | AgeLimit, TimeLimit, ShutdownNotifications, Callbacks, CurrentMessage | Стандартный middleware Dramatiq |
| 5 | Opt-in история попыток, CLI, retention | Lifecycle hooks |
| 6 | Атомарная пакетная отправка | Enqueue/dedup API |
| 7 | PostgreSQL interval scheduler, несколько процессов | Dedup + transactional enqueue |

Новые возможности являются расширениями IDDQueue. Этап 4 проверяет встроенные
middleware Dramatiq. Fixed interval scheduler не включает cron/calendar.
Дедупликация подавляет публикацию и не обещает exactly-once execution.
Heartbeat после подготовки плана авторизовал apply, sync и archive; все семь
этапов выполнены последовательно и отправлены в main отдельными commits.
Main specs синхронизированы, change архивирован 2026-10-03. Активных этапов этого
roadmap не осталось; новая функциональность требует отдельного OpenSpec change.
Публикация пакета не выполнялась и требует отдельного запроса.

## Ревью и сопровождение — 2026-10-04

Следующая работа авторизована пользователем через автоматизацию; порядок строго
последовательный, без реализации поверх активного запуска.

| Приоритет | Change | Состояние | Проверка |
| --- | --- | --- | --- |
| 1 | [fix-consumer-notification-consistency](changes/archive/2026-10-04-fix-consumer-notification-consistency/proposal.md) | R1–R4 исправлены; 130 tests passed; CI 37192114318 6/6 | [review/repro](changes/archive/2026-10-04-fix-consumer-notification-consistency/review.md), затем regressions/full suite/CI |
| 2 | [adopt-project-maintenance-practices](changes/archive/2026-10-04-adopt-project-maintenance-practices/proposal.md) | Оба этапа завершены: 131 tests, CI 37196894638 6/6; main spec синхронизирован, архив 2026-10-04 | CI/package/docs checks, policies и installed quickstart подтверждены |

Consumer исправлен и архивирован 2026-10-04. adopt-project-maintenance-practices завершён и архивирован 2026-10-04: CI, docs, policies и installed quickstart проверены. Доступных задач roadmap не осталось.
Docs/CI долги не дублируются в runtime change. Использовать Ponytail и Caveman,
не сокращая контракты/проверки. После каждого change — separate commit/push,
actual evidence, sync/archive. При отсутствии доступной работы автоматизация
приостанавливает себя; tag/PyPI publication по-прежнему требуют отдельного запроса.

## FastAPI — 2026-10-04

[document-fastapi-integration](changes/archive/2026-10-04-document-fastapi-integration/proposal.md):
выполнено: 147 tests passed, implementation CI 37229478184 и archive CI 37229692085: 6/6; архив 2026-10-04. Проверяемый пример lifespan + async endpoint
с отправкой через thread, отдельный worker, acceptance на PostgreSQL и документация
ограничения async-транзакций. Зависит от существующего broker; runtime API и схема
не меняются. [Задачи](changes/archive/2026-10-04-document-fastapi-integration/tasks.md).

## Release candidate — 2026-10-04

[prepare-rc-release](changes/archive/2026-10-05-prepare-rc-release/proposal.md): 0.13.0rc1 подготовлен, 147 tests passed, candidate CI 37230705441 и archive CI 37230962005: 6/6; архив 2026-10-05. Точные artifacts, release notes,
миграция, dev Pygments advisory, полный gate и actual CI перед передачей RC.
Tag/release/package upload — отдельный шаг. [Задачи](changes/archive/2026-10-05-prepare-rc-release/tasks.md).

## Публикация RC

[publish-rc-release](changes/archive/2026-10-05-publish-rc-release/proposal.md): GitHub prerelease
v0.13.0rc1 опубликован, remote hashes проверены. PyPI 0.13.0rc1 опубликован через OIDC, hashes и чистая index installation проверены;
обе операции завершены. Change архивирован 2026-10-05.

## Очистка репозитория

[clean-legacy-repository](changes/archive/2026-10-05-clean-legacy-repository/proposal.md): obsolete
Poetry runner/config/assets удалены, docs/dev setup обновлены; 147 tests passed.
Signed commit ef611d2, actual CI 37233116835 6/6; архив 2026-10-05.

## Актуализация документации

[reconcile-current-documentation](changes/archive/2026-10-05-reconcile-current-documentation/proposal.md):
current RC/install/status, API/migration limits и historical/performance context
исправлены; local docs/Ruff/lock/OpenSpec passed; signed d793ea8, CI 37233573387 6/6, архив 2026-10-05.

## Корневой README

[refresh-root-readme](changes/archive/2026-10-05-refresh-root-readme/proposal.md): короткий обзор и
проверенный quickstart, recipes отдельно; local docs/example/build/LICENSE passed.
Signed ade489b, actual CI 37234026977 6/6; архив 2026-10-05.

## Сайт документации

[publish-documentation-site](changes/archive/2026-10-05-publish-documentation-site/proposal.md): MkDocs/readthedocs,
пошаговые UI/CLI guides, strict CI и GitHub Pages опубликованы. Signed 46cf6bb; Tests
37237297166 6/6, Documentation 37237297097 success; public site/search проверены. Архив 2026-10-05.

## GitHub About

[update-github-project-page](changes/archive/2026-10-05-update-github-project-page/proposal.md): description, документация homepage и семь topics обновлены; GitHub readback подтверждён 2026-10-05.

## Разделение tooling и проекта

[clean-project-tooling-layout](changes/archive/2026-10-05-clean-project-tooling-layout/proposal.md): test actors и
Compose перенесены из корня, скиллы исключены из Git; 147 local tests passed. Signed
220c52f, Tests 37353269772 6/6, Documentation 37353269808 success; архив 2026-10-05.

## Ponytail simplification

[simplify-development-tooling](changes/archive/2026-10-05-simplify-development-tooling/proposal.md): удалён dev watch extra, redundant argparse defaults и docs Makefile; 147 local tests passed, CI 37359430071 6/6, Documentation 37359434787 success. Signed 0562f65; архив 2026-10-05. Watchdog остаётся зависимостью MkDocs.

## RC2 — 2026-10-06

[publish-rc2](changes/archive/2026-10-06-publish-rc2/proposal.md): 0.13.0rc2 опубликован на GitHub/PyPI. Candidate 784bd30; 147 tests, CI 37516016275 6/6; OIDC 37516414169 success. Remote hashes и clean index installation подтверждены, архив 2026-10-06.

## Исследование actor initialization — 2026-10-06

[investigate-actor-initialization](changes/archive/2026-10-07-investigate-actor-initialization/proposal.md): подтверждена ранняя привязка Dramatiq actor и отсутствие automatic rebind; план native/deferred alternatives, позднего DSN, доменных actors, одного bootstrap, штатных multi-process workers и Docker deployment; FastAPI optional. Выбран и реализован Domain API в add-domain-actors. Task 2.6 проверен 2026-10-07 на Colima containerd: Dockerfile/default CMD, две billing replicas по два процесса, queue isolation, connection samples и graceful shutdown. Signed c33b461, actual Tests 37533505783 6/6, Documentation 37533505839 success. Все 11 tasks завершены; архив 2026-10-07.

## Domain actors — 2026-10-07

[add-domain-actors](changes/archive/2026-10-07-add-domain-actors/proposal.md): реализация Domain queue/qualified names
и late startup registration, native Actors, framework-independent multi-domain worker/Docker example.
Завершено и архивировано 2026-10-07: 158 local tests, полный gate, signed a38e127; Tests 37531822792 6/6, Documentation 37531822886 success. Main spec синхронизирована. API не входит в опубликованный RC2.

## RC3 — 2026-10-07

[publish-rc3](changes/archive/2026-10-07-publish-rc3/proposal.md): 0.13.0rc3 опубликован на GitHub/PyPI с Domain API. Candidate 911ca1a; 158 local tests, CI 37536626612 6/6; OIDC 37537043153 success. Remote hashes/clean index installation/quickstart проверены; архив 2026-10-07. RC1/RC2 неизменны.
