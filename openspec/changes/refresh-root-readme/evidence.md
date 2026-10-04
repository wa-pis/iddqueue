## Local verification

README: 157 lines, published 0.13.0rc1, install/worker/producer/result quickstart, limits and docs navigation; comparison anchor and upstream credits/LICENSE preserved.
Detailed recipes moved to docs/recipes.md (569 lines). Exact original section equality verified after changing only relative LICENSE link; internal user-guide/API/index links updated.

Exact README fenced actor and producer extracted by /tmp/verify-iddqueue-readme.py. PyPI-installed 0.13.0rc1 in /tmp/iddqueue-pypi-rc-install, Python 3.13.14; dedicated PG14.20 localhost:55432 fresh iddqueue_readme DB. CLI init succeeds; separate spawned Dramatiq worker, published UUID, result 5. Temporary working directory outside checkout. Worker stopped, database removed, PostgreSQL stopped. shell uv wrappers represented by the corresponding installed executables; actor/producer Python unchanged.

Docs checker: exit 0. Ruff full configured paths: passed. uv lock --check: exit 0. strict OpenSpec 19/19, git diff --check: exit 0.
uv build --out-dir /tmp/iddqueue-readme-build: wheel/sdist success; check_license.py both: passed. Published dist/0.13.0rc1 and release assets not replaced. This docs build is not a new package publication; PyPI original RC README metadata remains tied to its original artifact.
Actual full matrix CI pending; runtime not changed.
