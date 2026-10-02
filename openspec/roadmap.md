# План развития PostgreSQL-проекта

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

[extend-postgres-capabilities](changes/extend-postgres-capabilities/proposal.md) —
этап 1 завершён (80 tests passed, все шесть CI jobs run 37063065568 success); этап 2 завершён (87 tests passed, шесть CI jobs run 37065548460 success); этап 3 завершён (97 tests passed, шесть CI jobs run 37069326903 success); этапы 4–7 не начаты. Proposal, design, семь delta specs и
[tasks](changes/extend-postgres-capabilities/tasks.md) описывают этапы.
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
Heartbeat после подготовки плана авторизовал переход к apply; работа выполняется последовательно.
