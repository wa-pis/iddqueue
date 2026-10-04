## Context

Текущий package version — 0.13.0; upstream tags заканчиваются на v0.12.0, GitHub releases в wa-pis/iddqueue отсутствуют. Последняя implementation/archive CI FastAPI прошла 6/6, локально 147 tests. Детали мотивации — proposal.md.

## Goals / Non-Goals

**Goals:** подготовленный 0.13.0rc1, точные проверенные artifacts и воспроизводимая инструкция установки RC.

**Non-Goals:** новый runtime функционал, изменение private visibility, публикация, release tag и новый контейнерный/publishing pipeline.

## Decisions

- Номер первого кандидата — 0.13.0rc1: сохраняется текущий цикл 0.13.0, применяется PEP 440 prerelease. Это рабочая версия плана, а не факт публикации. Не использовать rc как произвольный suffix вне package metadata.
- Notes выделяют RC и его предварительный статус, перечисляют новые возможности, SQL migration/rollback ограничения, at-least-once, ID-only уведомления и необходимость обновить всех участников, async publication через thread и ограничение AsyncConnection. Текущая comparison table остаётся историческим baseline; новые инструкции установки используют RC явно.
- Собирать в отдельный каталог конкретного кандидата, не передавать glob всех старых dist/*.whl в check_package.py. Идентифицировать wheel/sdist по metadata version; проверять LICENSE и SQL resources, CLI == 0.13.0rc1, чистую установку вне checkout, installed quickstart и base/monitoring profiles. Для prerelease установки передавать точный wheel или точное version constraint.
- Обновить только dev Pygments: GitHub alert #2, severity low, ReDoS GUID matching, patched 2.20.0. Перед изменением повторно проверить advisory и доступность исправленного пакета; не обновлять весь runtime lock. Если исправленная версия недоступна, записать блокер подготовки вместо заявления об исправлении.
- Использовать существующие release gate и шесть CI combinations. Локальные результаты dirty tree не выдавать за проверку parent commit. Финальный candidate commit должен иметь clean tree и успешный actual GitHub CI; evidence-only commits отдельно отличать от проверяемого runtime/package candidate.
- Checksums и полные SHA записывать в release evidence после сборки; новые сборки могут иметь другие hashes. Не создавать tags/releases автоматически: запрос пользователя сейчас относится к подготовке, destination публикации и доступность приватного проекта остаются отдельными решениями.

## Risks / Trade-offs

- Старые 0.13.0 artifacts смешиваются с RC → отдельный каталог и выбор точных имён/metadata.
- Предварительная версия воспринимается как стабильная → явно отметить RC и тестовую установку, не обещать production readiness.
- Dev advisory остаётся open → проверять исправленную locked версию и remote alert после push, учитывать задержку GitHub; не считать исчезновение warning единственным доказательством.

## Migration Plan

Пользовательские шаги берутся из docs/migration.md; изменение версии само не меняет SQL. Откат RC к upstream не обещается без восстановления backup и учёта изменений namespace/schema. Публикация после подготовки требует отдельного запроса с выбранным каналом.
