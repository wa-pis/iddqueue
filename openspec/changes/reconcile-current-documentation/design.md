## Context

Published version metadata/PyPI 0.13.0rc1; current CLI и init используют полную schema. Original docs/changelog.rst доступен в baseline commit 80b1a490d0a494925a9f8be399a11b38cee5480a. docs/why.rst содержит старые hardware benchmarks и неверные blanket AMQP/PostgreSQL assertions, не подтверждённые текущими tests.

## Goals / Non-Goals

**Goals:** однозначные опубликованная версия, установка, historical context, runtime limits и актуальное publishing состояние.

**Non-Goals:** новые runtime возможности, новые performance claims, изменение release artifacts, переписывание архивных OpenSpec команд как будто они исполнялись иначе.

## Decisions

Сопоставить docs с pyproject/CLI/source и actual release evidence. Restore historical changelog из baseline; отметить, что его Unreleased — upstream snapshot, не статус IDDQueue. Переписать why в текущую техническую мотивацию и trade-offs без неподтверждённых benchmarks/claims про AMQP/PgQ. Example install проверять с опубликованного exact version; selectors CLI/API проверять read-only, без shared DB. Docs checker + full CI подтверждают links и regression suite; новых docs-only unit tests не требуется.

## Risks / Trade-offs

Исторические upstream сведения легко принять за current → отдельный header/ссылка на CHANGELOG.md. Existing screenshots/package README на PyPI принадлежат immutable RC → обновлённые docs идут в main, release files не заменяются.
