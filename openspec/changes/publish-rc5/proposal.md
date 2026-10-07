## Why

Пользователь авторизовал выпуск следующего RC после async transactional enqueue и security diff review. Нужны проверенный candidate 0.13.0rc5, актуальная документация и immutable GitHub/PyPI artifacts.

## What Changes

- Версия 0.13.0rc5, lock, release notes/install guides и описание GitHub About с async publication.
- Полный release gate, signed candidate/tag, фактический CI.
- GitHub prerelease и PyPI OIDC exact wheel/sdist без rebuild; readback hashes и clean index async recipe acceptance.

## Capabilities

### New Capabilities
Нет.

### Modified Capabilities
Нет: выпуск существующих возможностей, skip_specs: true.

## Impact

Metadata/docs/publish workflow; без DDL и runtime изменений. RC1–RC4 artifacts неизменны. Security diff e56c6b1..414e1c6 завершён: findings0, static20changed paths; это не полный аудит dependency CVEs или production grants.
