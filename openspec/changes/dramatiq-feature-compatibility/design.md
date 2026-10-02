## Context

Pipelines, groups, async actors и on_retry_exhausted реализованы в Dramatiq, но не подтверждены нашим набором интеграционных тестов. Нужны проверенные сценарии использования PostgreSQL broker. Текущая база — Psycopg 3 и Dramatiq 2.2.1; локальная миграция уже проверена. См. proposal.md и delta spec.

## Goals / Non-Goals

**Goals:** Совместимость со стандартными возможностями Dramatiq, проверенная на реальном PostgreSQL.

**Non-Goals:** замена стандартного worker Dramatiq, exactly-once, автоматическая публикация релиза.

## Decisions

Использовать существующие Pipelines, Results, Retries и опциональный AsyncIO; не строить новый orchestration engine. Проверять реальные workers и PostgreSQL. GroupCallbacks тестировать отдельно после postgres-coordination. Асинхронность actor не делает sync broker асинхронным: отдельный AsyncConnection broker в scope не входит. Приоритет actors уже применяется очередью worker в рамках полученных сообщений; глобальный SQL-priority scheduler в scope не входит.

## Risks / Trade-offs

Ошибки и повторная доставка отдельных шагов могут повторить обработку: остаётся at-least-once. Async actor не должен блокировать event loop синхронным I/O; примеры используют подходящие клиентские операции.

## Migration Plan

Выполнить tasks.md, повторить релевантные интеграционные проверки и сборку. Для изменения SQL подготовить явную миграцию существующей базы и обратимый путь до включения новой функции. Новые опциональные возможности включаются явно. После проверки синхронизировать delta spec и архивировать change.
