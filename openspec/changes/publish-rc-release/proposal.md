## Why

Пользователь разрешил выпуск проверенного 0.13.0rc1 на GitHub и PyPI и сделал wa-pis/iddqueue публичным. Необходимо фиксировать отдельные факты публикации и доступ к package index.

## What Changes

- Выпустить GitHub prerelease v0.13.0rc1 из проверенного candidate SHA с wheel/sdist/SHA256SUMS.
- Опубликовать те же артефакты на PyPI после получения безопасно настроенной аутентификации.
- Проверить remote hashes/version и записать evidence; не выдавать GitHub release за PyPI publication.

## Capabilities

### New Capabilities

Нет.

### Modified Capabilities

Нет: операция выпуска, skip_specs=true.

## Impact

GitHub tag/release/assets и PyPI distribution; runtime API и содержимое проверенных artifacts не меняются.
