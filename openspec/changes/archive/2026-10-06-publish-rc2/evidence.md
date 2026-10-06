# Evidence

2026-10-06: полный local release gate прошёл: 147 tests, dedicated PostgreSQL 14.20 / Python 3.13.14, Ruff/lock/docs/MkDocs/OpenSpec/build/LICENSE, clean installed base/monitoring wheel acceptance и quickstart. Candidate CI и публикация pending.

Candidate: 784bd3044d1a880eb863a6547a7edf4d62bd2bc6, signed commit/tag v0.13.0rc2. Tests 37516016275 success 6/6; Documentation 37516016207 success. Gate: 147 tests passed in 51.48s. Build после candidate commit воспроизвёл те же hashes.

Wheel SHA256 de844d3544507c6c3947dde01ee940be0dcf25ee5bd7013285f28eb1535a3d1a; sdist SHA256 8f3f36dbb542715c6b43366ced0a10b67abb2259345710b53e87b18f0ee93dd2. GitHub release download/SHA256SUMS проверены.

Fixed publish workflow signed commit 16e91ba; PyPI OIDC run 37516414169 success. PyPI JSON hashes совпали с remote GitHub artifacts. Clean installation /tmp/iddqueue-rc2-index outside checkout reports 0.13.0rc2; import path подтверждён. Installed PyPI quickstart проверил six tables, enqueue и result=5. RC1 release/tag/assets не менялись. Specs behavior unchanged, deltas отсутствуют.
