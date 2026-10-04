## Context

См. proposal.md. Исходная версия для сравнения — опубликованный dramatiq-pg 0.12.0 (PyPI: https://pypi.org/project/dramatiq-pg/0.12.0/), исходный проект https://gitlab.com/dalibo/dramatiq-pg. Исторический baseline форка: 80b1a490d0a494925a9f8be399a11b38cee5480a. Текущий IDDQueue проверяется по исходникам, main specs и архивным evidence, а не только по roadmap.

## Goals / Non-Goals

**Goals:** видимое происхождение; проверяемое сравнение; переход с сохранением данных и явными несовместимостями.

**Non-Goals:** новые runtime-фичи, исправление security-находки, публикация, обещания производительности без benchmark, совместимость сторонней Django-интеграции без проверки.

## Decisions

Одна компактная таблица в README и подробный docs/migration.md; не дублировать подробную инструкцию в нескольких местах. Документация продукта на английском, как существующие README/docs; OpenSpec на русском.

План строк таблицы (отсутствие возможности upstream подтверждать исходниками 0.12.0 перед финальной формулировкой):

| Область | Upstream baseline | IDDQueue / эффект |
| --- | --- | --- |
| PostgreSQL/JSONB, задержки, results, восстановление, CLI | Унаследованы | Сохранены; не выдавать за новые фичи |
| Драйвер и Python | Psycopg 2; Python >=3.6 | Синхронный Psycopg 3/pool; Python >=3.10 |
| Dramatiq | Проверить constraints исходной metadata | >=2.2.1,<3; проверенная совместимость middleware/composition |
| Транзакционная отправка | Проверить отсутствие публичного API | enqueue_in_transaction; бизнес-данные и задача в одной транзакции |
| Координация | Проверить исходный backend | PostgreSQL rate limits/barriers/GroupCallbacks без Redis |
| Операции | Базовые stats/purge/recover/flush | Диагностика/retry, pause/resume, cancellation, opt-in history |
| Публикация задач | Обычный enqueue | Dedup key/TTL и атомарные batches; не exactly-once |
| Расписание | Delay поддержан | Fixed-interval scheduler; не cron/calendar |
| Наблюдаемость | Проверить исходный API | Backlog/возраст, опциональный Prometheus |
| Namespace | Настраиваемая схема/таблица | Согласованные schema/prefix для storage/channels/locks; не ACL |
| Поддержка | Не объявлять upstream заброшенным | Фактическая CI-матрица Python 3.10/3.13/3.14 × PG14/18 |

## Risks / Trade-offs

- Непроверенное «upstream не умеет» → фиксированная версия, исходники и точечные ссылки/evidence для каждой строки.
- Смешение переименования с полной миграцией → отдельно описать imports/CLI и driver/storage upgrade; не повторять README-фразу об неизменных channels как гарантию совместимости со старым upstream во всех namespaces.
- Потеря данных при rollback → backup и изолированная rehearsal; не обещать запуск старого брокера на расширенной схеме с новыми состояниями.
- Неисправленная утечка NOTIFY → не заявлять confidentiality между ролями общей БД; отметить известное ограничение и отдельный remediation scope.

## Migration Plan

Руководство обязано последовательно описать: инвентаризация версии/DSN/schema/table/pool; backup; проверка восстановления; staging-копия; замена distribution/import/CLI; Psycopg 3 pool или broker-owned pool; остановка producers, scheduler, workers и result waiters; upgrade выбранной области с сохранением queue/results и опциональными таблицами; запуск всей области на одной версии; smoke задач/results/retry и counts; rollback через восстановление backup и согласованного старого окружения. Не использовать flush/purge как шаг перехода. Для отменённых/новых состояний не обещать бесшовный downgrade. Custom table mapping проверить по constructor/CLI и описать явно.
