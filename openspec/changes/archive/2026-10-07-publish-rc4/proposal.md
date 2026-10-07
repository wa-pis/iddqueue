## Why

Пользователь запросил RC4 и security review. После RC3 реализованы domain observability, optional SQLAlchemy adapter, debug kit и эксплуатационная документация; перед публикацией нужны security/readiness fixes и проверенный immutable candidate.

## What Changes

- Версия 0.13.0rc4, актуальные install/docs/release notes/changelog.
- Полный release gate, installed profiles и signed candidate/tag.
- GitHub prerelease и PyPI Trusted Publishing exact assets с проверкой hashes/index installation.

## Capabilities

### New Capabilities
Нет.

### Modified Capabilities
Нет: координация выпуска существующих возможностей, skip_specs: true.

## Impact

Package metadata/uv.lock/docs/publish.yml; ранее опубликованные RC неизменны. Publication авторизована пользователем; не выпускать до завершения fix-readiness-observation-gaps, fix-malformed-notification-handling и restrict-local-postgres-example.
