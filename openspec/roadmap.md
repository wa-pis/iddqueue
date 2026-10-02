# План развития PostgreSQL-проекта

Завершённые локальные этапы: transactional-enqueue, postgres-coordination. Проверки и ограничения — в соответствующих validation.md.

| Порядок | Change | Результат | Зависимость |
| --- | --- | --- | --- |
| 0 | [modernize-postgres-broker](changes/modernize-postgres-broker/tasks.md) | Psycopg 3, Dramatiq 2.2.1, новый GitHub-проект и CI | Базовая работа |
| 1 | [transactional-enqueue](changes/archive/2026-10-02-transactional-enqueue/proposal.md) | Выполнено: бизнес-данные и задача в одной транзакции | Runtime миграции |
| 2 | [postgres-coordination](changes/archive/2026-10-02-postgres-coordination/proposal.md) | Выполнено: лимиты, барьеры и group completion callbacks без Redis | Runtime миграции |
| 3 | [dramatiq-feature-compatibility](changes/dramatiq-feature-compatibility/proposal.md) | pipelines, groups, async actors, retry exhaustion callback, timedelta | Runtime; group callbacks после coordination |
| 4 | [failed-task-management](changes/failed-task-management/proposal.md) | ошибки, диагностика и выборочный retry | Runtime миграции |
| 5 | [postgres-queue-metrics](changes/postgres-queue-metrics/proposal.md) | Backlog и возраст задач, опциональный Prometheus | Runtime; согласовать metadata с failed-task-management |
| 6 | [result-namespace-isolation](changes/result-namespace-isolation/proposal.md) | Изоляция схем/префиксов, уведомлений, locks и результатов | Runtime; область хранения переиспользуется coordination/metrics |
Порядок рекомендованный: первый этап — транзакционная отправка и backend координации. Изоляцию namespace желательно включить до многопользовательского использования и согласовать до стабилизации схемы coordination. Возможности middleware проверяются через стандартные реализации Dramatiq, без собственного orchestration engine. Actor priority документируется как локальный порядок prefetched-сообщений worker; глобальный планировщик приоритетов не включён.

Идентичность нового GitHub-репозитория и пакета остаётся отдельным решением пользователя. Публикация в PyPI не входит в этот план без отдельного запроса.
