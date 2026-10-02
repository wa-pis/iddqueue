## Context

LICENSE содержит PostgreSQL Licence, Copyright (c) 2019, DALIBO и разрешение
use/copy/modify/distribute при сохранении copyright и полного текста.
pyproject.toml уже содержит license="PostgreSQL". Runtime миграция и шесть
фич завершены; GitHub/package identity остаются открытыми.

## Goals / Non-Goals

**Goals:** сохранить лицензию и происхождение в распространяемых артефактах,
подтвердить это воспроизводимой проверкой сборки.

**Non-Goals:** смена лицензии, выбор нового владельца copyright без данных,
юридическая гарантия отсутствия исков, публикация PyPI, переименование проекта.

## Decisions

- Сохранить существующий LICENSE. Новое copyright на собственные изменения
  добавляется только при известных авторских данных, без удаления исходного.
- Добавить README attribution и краткие условия распространения с ссылками
  на upstream LICENSE и официальный текст PostgreSQL License.
- Проверить wheel через zipfile и sdist через tarfile: найти LICENSE и
  сопоставить полное содержимое с сохранённым upstream текстом.
- При отсутствии LICENSE исправить только необходимую packaging настройку.
- Сохранить проверку артефактов в CI после сборки; runtime PostgreSQL-тесты
  для изменения только документации/упаковки не нужны.
- Лицензии зависимостей независимы; не объявлять их автоматически PostgreSQL.

## Risks / Trade-offs

Включение LICENSE в Git не доказывает его включение в wheel. Credits нельзя
заменять именем нового владельца репозитория. Источник разрешений — конкретный
текст лицензии, а не обещание полной правовой безопасности.

## Migration Plan

Изменений SQL нет. Реализовать tasks после перехода к apply; проверить
упаковку и OpenSpec, сделать отдельный коммит, синхронизировать и архивировать.
Существующие публикации не заявляются проверенными этим планом.

## References

- Исходный LICENSE: https://gitlab.com/dalibo/dramatiq-pg/-/blob/master/LICENSE
- Официальный текст: https://www.postgresql.org/about/licence/
- Upstream commit: 80b1a490d0a494925a9f8be399a11b38cee5480a
