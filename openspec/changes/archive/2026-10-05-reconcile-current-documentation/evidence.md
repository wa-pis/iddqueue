## Findings and corrections

- README comparison header/table, migration target: current published 0.13.0rc1, not a published stable 0.13.0.
- migration install: PyPI published, exact version with uv venv; stale local 0.13.0 wheel and false unpublished claim removed. README/get-started installation explicitly creates a venv.
- README feature wording: persistence/at-least-once and probabilistic idle retention instead of unconditional reliability/cleanup implications.
- API: schema/prefix/queue_control/attempt_history parameters documented; pool ownership, namespace-only versus full schema upgrade distinguished using broker/results/schema source.
- docs/changelog.rst restored exactly from baseline 80b1a490d0a494925a9f8be399a11b38cee5480a plus historical note; own features belong in CHANGELOG.md. Equality after removing note confirmed.
- why.rst: removed old laptop figures presented as current, blanket AMQP/PgQ claims and single-INSERT/UPDATE cost claims; actual ID-only notifications, SQL claims/session locks, feature tables, at-least-once and workload limits documented. Inherited perf scripts explicitly unvalidated exploratory tools.
- Publishing docs now state successful first OIDC publication and configured publisher, discourage rerunning immutable RC; initial pending-publisher setup remains clearly historical/reference.
- SUPPORT removes private access claim. Index/release describe published RC. OpenSpec current context now records 147 tests and latest passed 6/6 matrix, preserving historical archives.

## Local verification

`python scripts/check_docs.py`: exit 0. Ruff full configured paths: passed. `uv lock --check`: exit 0. Strict OpenSpec 19/19, `git diff --check`: exit 0. Published index-installed package /tmp/iddqueue-pypi-rc-install CLI --version=0.13.0rc1, --help successful. Exact index installation/remote hashes were validated in publication evidence; no new package upload/build performed here.
Read-only stale phrase search confirms removed unpublished/private/stable-version/old performance assertions in live docs. Runtime code unchanged. Full unit/func/PostgreSQL/build/install verification delegated to existing actual GitHub CI for this docs commit; results not yet asserted.

## Completion

Signed commit d793ea890160ecc180d4cf9522969c28578f1788: git verify-commit Good SSH signature, push main successful.
[Tests 37233573387](https://github.com/wa-pis/iddqueue/actions/runs/37233573387): completed/success, 6/6, full tests/build/install/doc gate.
Jobs: 3.14/PG18 111528149459, 3.13/PG14 111528149514, 3.10/PG18 111528149518, 3.14/PG14 111528149534, 3.13/PG18 111528149587, 3.10/PG14 111528149623 — все success.
GitHub v0.13.0rc1 release body обновлён: successful PyPI publication, exact install, public repo и актуальные docs links; readback подтвердил. Assets/tag не изменены. Published package README metadata belongs to immutable original RC artifact; corrections are repository/live release docs, not a replacement upload of 0.13.0rc1.
Delta specs отсутствуют; docs-only change завершён.
