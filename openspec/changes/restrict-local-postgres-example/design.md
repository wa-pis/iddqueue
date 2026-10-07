## Context

Локальный walkthrough подключается к localhost, но ports 5432:5432 публикует БД на всех интерфейсах.

## Decisions

Использовать native Compose host IP 127.0.0.1. Сохраняются существующие локальные credentials/port и disposable evaluation workflow; не добавлять security framework.

## Risks / Trade-offs

Другие машины больше не подключаются по умолчанию; это соответствует local-only example. Контейнеры той же compose network сохраняют service connectivity.
