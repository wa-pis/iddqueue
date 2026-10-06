## Why

Приложение может создавать таблицы через собственный migration runner. Пользователь просит явно зафиксировать этот режим и отсутствие необходимости DDL для RC2 -> RC3.

## What Changes

- Описать существующий контракт: broker не создаёт и не обновляет schema автоматически; init/upgrade — явные административные действия.
- Документировать внешнее применение generate_init_sql/generate_upgrade_sql с согласованными schema/prefix.
- Зафиксировать upgrade RC2 -> RC3 без DDL; Domain использует существующие queue_name и actor_name.
- Не добавлять auto_migrate/skip_migration flags: отключать автоматическую миграцию уже не требуется.

## Capabilities

### Modified Capabilities

- project-distribution: явное управление схемой и внешние миграции, описание существующего поведения.

## Impact

Docs/spec и проверки существующего контракта; runtime API, зависимости, структура таблиц и опубликованный RC3 не меняются.
