## Decisions

Переиспользовать release gate и OIDC workflow. Сначала подписанный candidate commit и actual CI, затем build с этого commit, LICENSE/installed acceptance и hashes. Signed tag v0.13.0rc2 на candidate; GitHub release с точными assets. Publish workflow обновить fixed SHA/hashes, отдельным signed commit, выполнить вручную. Проверить PyPI JSON hashes и clean installation вне checkout.

## Verification

147 unit/func tests на dedicated PostgreSQL, Ruff/lock/docs/MkDocs/strict OpenSpec/build/LICENSE/installed wheel. Actual CI 6/6 и Pages. Public docs переключить на RC2, RC1 historical notes сохранить.
