# План развития PostgreSQL-проекта

Транзакционная отправка реализована и архивирована 2026-10-02 (38 тестов прошли). Координация PostgreSQL реализована и архивирована 2026-10-02 (45 тестов прошли). Совместимость middleware и композиции Dramatiq проверена и архивирована 2026-10-02 (51 тест прошёл). Диагностика ошибок и выборочный retry реализованы и архивированы 2026-10-02 (56 тестов прошли). Метрики очереди реализованы и архивированы 2026-10-02 (58 тестов прошли). Изоляция namespace реализована и архивирована 2026-10-02 (63 теста прошли). Все шесть запланированных локальных фич завершены; GitHub setup остаётся в baseline change. Выполненная миграция и оставшиеся шаги GitHub отражены отдельно в `modernize-postgres-broker`.

| Порядок | Change | Результат | Зависимость |
| --- | --- | --- | --- |
| 0 | [modernize-postgres-broker](changes/modernize-postgres-broker/tasks.md) | Psycopg 3, Dramatiq 2.2.1, новый GitHub-проект и CI | Базовая работа |
| 1 | [transactional-enqueue](changes/archive/2026-10-02-transactional-enqueue/proposal.md) | Выполнено: бизнес-данные и задача в одной транзакции | Runtime миграции |
| 2 | [postgres-coordination](changes/archive/2026-10-02-postgres-coordination/proposal.md) | Выполнено: лимиты, барьеры и group completion callbacks без Redis | Runtime миграции |
| 3 | [dramatiq-feature-compatibility](changes/archive/2026-10-02-dramatiq-feature-compatibility/proposal.md) | Выполнено: pipelines, groups, async actors, retry exhaustion callback, timedelta | Runtime; group callbacks после coordination |
| 4 | [failed-task-management](changes/archive/2026-10-02-failed-task-management/proposal.md) | Выполнено: ошибки, диагностика и выборочный retry | Runtime миграции |
| 5 | [postgres-queue-metrics](changes/archive/2026-10-02-postgres-queue-metrics/proposal.md) | Выполнено: backlog и возраст задач, опциональный Prometheus | Runtime; согласовать metadata с failed-task-management |
| 6 | [result-namespace-isolation](changes/archive/2026-10-02-result-namespace-isolation/proposal.md) | Выполнено: изоляция схем/префиксов, уведомлений, locks и результатов | Runtime; область хранения переиспользуется coordination/metrics |

Порядок рекомендованный: первый этап — транзакционная отправка и backend координации. Изоляцию namespace желательно включить до многопользовательского использования и согласовать до стабилизации схемы coordination. Возможности middleware проверяются через стандартные реализации Dramatiq, без собственного orchestration engine. Actor priority документируется как локальный порядок prefetched-сообщений worker; глобальный планировщик приоритетов не включён.

Идентичность нового GitHub-репозитория и пакета остаётся отдельным решением пользователя. Публикация в PyPI не входит в этот план без отдельного запроса.

CLI init/stats/purge/recover/flush на нестандартных schema/prefix проверены 2026-10-02: 64 теста прошли. Все независимые локальные задачи baseline завершены; задачи 5.1–5.5 ожидают решений по GitHub и идентичности пакета.

## Сохранение лицензии форка

[preserve-fork-license](changes/preserve-fork-license/proposal.md) — новый план: сохранение полного LICENSE/copyright DALIBO в исходниках и wheel/sdist, README attribution и проверка упаковки в CI. Реализация ещё не выполнена; публикация не включена. Этот этап независим от решения об имени GitHub-проекта.
