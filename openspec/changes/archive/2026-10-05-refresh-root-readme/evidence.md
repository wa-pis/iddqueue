## Local verification

README: 157 lines, published 0.13.0rc1, install/worker/producer/result quickstart, limits and docs navigation; comparison anchor and upstream credits/LICENSE preserved.
Detailed recipes moved to docs/recipes.md (569 lines). Exact original section equality verified after changing only relative LICENSE link; internal user-guide/API/index links updated.

Exact README fenced actor and producer extracted by /tmp/verify-iddqueue-readme.py. PyPI-installed 0.13.0rc1 in /tmp/iddqueue-pypi-rc-install, Python 3.13.14; dedicated PG14.20 localhost:55432 fresh iddqueue_readme DB. CLI init succeeds; separate spawned Dramatiq worker, published UUID, result 5. Temporary working directory outside checkout. Worker stopped, database removed, PostgreSQL stopped. shell uv wrappers represented by the corresponding installed executables; actor/producer Python unchanged.

Docs checker: exit 0. Ruff full configured paths: passed. uv lock --check: exit 0. strict OpenSpec 19/19, git diff --check: exit 0.
uv build --out-dir /tmp/iddqueue-readme-build: wheel/sdist success; check_license.py both: passed. Published dist/0.13.0rc1 and release assets not replaced. This docs build is not a new package publication; PyPI original RC README metadata remains tied to its original artifact.
Actual full matrix CI pending; runtime not changed.

## Remote verification

Signed commit ade489bb8fd4e55103175cfea6ed250b74a5d55b, verify-commit Good SSH signature, push main successful.
[Tests 37234026977](https://github.com/wa-pis/iddqueue/actions/runs/37234026977): completed/success, 6/6, verified by gh run view (watch returned nonzero; authoritative readback successful).
Jobs: 3.10/PG14 111529466014, 3.14/PG14 111529466216, 3.13/PG18 111529466230, 3.14/PG18 111529466255, 3.13/PG14 111529466301, 3.10/PG18 111529466306 — все success.
All tasks complete; no delta specs. Archive bookkeeping changes only.
