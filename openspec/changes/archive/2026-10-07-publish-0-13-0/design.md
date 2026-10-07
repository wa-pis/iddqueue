## Context

RC5 опубликован и проверен: 200 tests, CI 6/6, clean PyPI install и async actor recipe. GitHub wa-pis/iddqueue public/main; publisher publish.yml использует environment pypi.

## Goals / Non-Goals

Выпустить 0.13.0 с полными release notes и сохранить проверенный runtime RC5. Новые функции, DDL и обновления dependencies не входят в выпуск.

## Decisions

Переиспользовать scripts/check_release.sh на выделенном PG14. Собрать dist/0.13.0, подписать candidate после gate, дождаться шести CI jobs и Documentation. Подписанный tag указывает на точный candidate. GitHub release без prerelease, exact wheel/sdist/SHA256SUMS. Publisher отдельным signed commit pin version/candidate/hash и OIDC upload без rebuild. Проверить GitHub скачиванием, PyPI metadata/hashes, чистой index installation и async recipe вне checkout.

## Risks / Trade-offs

PyPI version immutable: после неизвестного исхода проверить registry перед повторным запуском. Прежние RC artifacts/tag не менять. Задержка simple index: дождаться propagation без reupload. Прошлый security diff RC4..RC5 без findings; этот release не является новым полным security audit.

## Migration Plan

С RC5 только обновление пакета; SQL/runtime не меняются. Переход с upstream по существующему migration guide, не обещать отсутствие миграции для произвольных старых версий. Rollback на RC5 через pin версии.
