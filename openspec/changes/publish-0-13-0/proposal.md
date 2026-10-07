## Why

Пользователь авторизовал стабильный выпуск 0.13.0 после опубликованного RC5. Нужны полноценные release notes, проверенные immutable artifacts и подтверждённая публикация GitHub/PyPI.

## What Changes

- Версия/lock/актуальные installation guides и release notes 0.13.0; история RC сохранена.
- Полный release gate, подписанные candidate/tag и фактический CI.
- GitHub stable release и PyPI OIDC из тех же wheel/sdist, readback SHA256 и clean installation.

## Capabilities

### New Capabilities
Нет.

### Modified Capabilities
Нет: skip_specs: true, существующее поведение RC5 без изменений.

## Impact

Metadata/docs/publisher workflow. Без DDL, новых dependencies и runtime изменений. PostgreSQL LICENSE и credits сохраняются. Пользователь сообщил, что исправил Trusted Publisher; workflow использует environment pypi, успешный OIDC upload проверяется фактически.
