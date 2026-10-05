## Why

Пользователь просит убрать из корня test-only example/Compose и исключить скиллы агента из репозитория.

## What Changes

Перенести actors в tests/func/actors.py, убрать неиспользуемый demo/debugger; обновить imports и subprocess worker module. Перенести Compose в examples/postgres/compose.yml, обновить документацию. Убрать .agents/skills из Git, оставить локальные ignored копии.

## Capabilities

Публичное поведение пакета и существующие specs не меняются.

## Impact

Тесты, development layout, документация, Git tracking. Лицензия и upstream credits сохраняются; новые зависимости не нужны.
