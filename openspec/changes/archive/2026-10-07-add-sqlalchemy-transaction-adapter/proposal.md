## Why

Приложения с SQLAlchemy хотят атомарно сохранять бизнес-данные и задачу без отдельного broker commit. Существующий enqueue_in_transaction принимает активный Psycopg 3 connection.

## What Changes

Optional SQLAlchemy 2.x adapter для синхронных Connection/Session с PostgreSQL psycopg dialect; переиспользовать существующий transactional enqueue. Драйвер/broker и worker остаются Psycopg 3. AsyncSession/AsyncConnection, asyncpg/psycopg2 и Engine как замена broker pool не входят в первый этап.

## Capabilities

### Modified Capabilities
- transactional-task-publishing: SQLAlchemy input и сохранение caller ownership.

## Impact

Optional extra/module, compatibility tests/docs/lock. Новая обязательная зависимость и DDL не нужны. RC3 неизменен.
