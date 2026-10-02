## Why

Форк разрешён PostgreSQL License исходного dramatiq-pg. Нужно закрепить
сохранение copyright DALIBO и полного текста разрешения/отказа от гарантий
в исходниках и публикуемых артефактах, а также происхождение проекта.
Текущий LICENSE сохранён; включение в wheel/sdist подтверждено локальной сборкой.

## What Changes

- Сохранить PostgreSQL License и исходное copyright notice без удаления.
- Документировать происхождение форка и разрешённые использование,
  изменение и распространение, включая коммерческое, при соблюдении лицензии.
- Проверить включение полного LICENSE в wheel/sdist и метаданные лицензии.
- Добавить проверку упаковки, предотвращающую потерю LICENSE при сборке.
- Отдельно обозначить лицензии зависимостей; не обещать отсутствие любых исков.

## Capabilities

### New Capabilities

- `fork-license-preservation`: Сохранение лицензии и attribution форка.

### Modified Capabilities

Нет; baseline project-distribution остаётся активным до GitHub setup.

## Impact

README, packaging metadata при необходимости, проверка wheel/sdist, OpenSpec.
Runtime и SQL не меняются. GitHub/package identity ещё не согласованы;
публикация в PyPI не разрешается этим change. Реализовано локально; см. validation.md.
