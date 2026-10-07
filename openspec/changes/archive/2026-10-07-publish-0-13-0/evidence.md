## Local release gate

Дата: 2026-10-07. Python 3.13.14, выделенный PostgreSQL 14.20 /tmp/iddqueue-domains-pg, port55433/max_connections120, databasepostgres. Gate scripts/check_release.sh exit0, лог /tmp/iddqueue-stable-gate.log. PGHOST=127.0.0.1 PGPORT=55433 PGUSER=postgres PGDATABASE=postgres IDDQUEUE_TEST_DATABASE=dedicated UV_PROJECT_ENVIRONMENT=/tmp/iddqueue-docsite-env UV_CACHE_DIR=/tmp/iddqueue-uv-cache PYTHON=/tmp/iddqueue-docsite-env/bin/python UV=/opt/homebrew/bin/uv.

200 tests passed; Ruff, uv lock/sync/pip check, async actor recipe, strict docs/OpenSpec20/20, build/LICENSE, isolated base/monitoring/SQLAlchemy wheel installs и quickstart result5/cleanup passed. uv.lock изменил только root version, dependencies сохранены. Побайтовое сравнение wheel RC5/stable: все23 runtime/SQL files identical. Gate выполнил проверку dirty release tree поверх7d2d206; candidate SHA будет записан после signed commit и подтверждён remote CI.

Предыдущий security diff RC4..RC5: 20 paths,0findings; новый runtime diff пуст. Новый полный security scan не выполнялся.

## Artifacts

eaa5e6c855485249908c67eaab24ddfd71b762f2030cefe7cba31f5ec68c1826  iddqueue-0.13.0-py3-none-any.whl
8531940c89b29e88161e547f1d441b13f52f3c01a8330de315a91862356b4ddb  iddqueue-0.13.0.tar.gz

Remote CI и publication ещё не проверены.

## Candidate CI

Signed candidate09a8393377f5335b3cf0eb85c08845cbb9751f3c pushedmain, GitHub signatureverifiedtrue/reasonvalid. Tests37675872261 success: Python3.10/3.13/3.14 × PostgreSQL14/18, all6jobs success. Documentation37675872233build/deploysuccess. PublicHTTP release-0.13.0/get-started checked. Local200tests55.87s.

## GitHub stable release

Signedtagv0.13.0 goodSSHsignature, targetcandidate09a8393377f5335b3cf0eb85c08845cbb9751f3c. https://github.com/wa-pis/iddqueue/releases/tag/v0.13.0 isPrereleasefalse/isDraftfalse; wheel36687bytes,sdist27984bytes,SHA256SUMS188bytes. All3assetsdownloaded/tmp/iddqueue-stable-github-readback, byte-for-byte matchedlocal. Release notes include features/upgrade/limits/candidateCI/hashes.

## PyPI и registry acceptance

Signedpublisher28f0e4641aaef4096ff7fe5a9355732f8e8ae6cc pushedmain; remote publish.yml fetched черезGitHubAPI и byte-compared с local передdispatch. OIDC37676419804success, environmentpypi. PyPI https://pypi.org/project/iddqueue/0.13.0/: version0.13.0/license_expressionPostgreSQL/обаSHA256matched; JSONreadback/tmp/iddqueue-stable-pypi.json.

Cleanvenv/tmp/iddqueue-stable-index-check внеcheckout: uvpipinstall --no-cache --default-indexhttps://pypi.org/simple/ iddqueue[binary,monitoring,sqlalchemy]==0.13.0. Девятьpackages installed; compatibilitycheckpassed. Metadata/version/licenseconfirmed,direct_url.jsonabsent,bothasyncmethods coroutineconfirmed. Freshresolved versions: dramatiq2.2.1,iddqueue0.13.0,prometheus-client0.26.0,psycopg3.3.6,psycopg-binary3.3.6,psycopg-pool3.3.3,sqlalchemy2.1.4,tenacity9.2.1,typing-extensions4.16.0. Lockdependencies unchanged; freshindexresolution закономерно использует доступные версии в пределах existingranges.

Copiedquickstart/async-transactionexecutedbin/python-I: installedpackage only, dedicatedPG14. Six tables/enqueue/result5 и businesscommit/asyncactorresultpassed; bothworkerstopped, isolatedschemasremoved.

Signedtag Tests37676249343success; publisherDocumentation37676365231success. PublisherTests37676365249 success/all6jobs. GitHub latest tagv0.13.0, isPrereleasefalse; release accepted.

## Archive

Change архивирован2026-10-07 послефактическойpublication/acceptance; alltaskscomplete. Release notes добавленывdocs/changelog/GitHubRelease, readbackGitHubbodyconfirmedOIDCrunlink. Безdeltas/main-specchanges.
