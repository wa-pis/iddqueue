# Release readiness

Build and checks do not create tags or publish a package. The repository is public;
0.13.0rc1 is published on GitHub and PyPI. Future publication requires a separate
explicit request. See [Trusted Publishing](publishing.md).

1. Select the candidate commit; check `git status --short` and `git rev-parse HEAD`.
   Review user changes/migrations in [CHANGELOG](../CHANGELOG.md) and
   [support policy](../SUPPORT.md). Preserve license and credits.
2. Install dev dependencies, configure a dedicated PostgreSQL with PG* variables
   and prepare fresh storage as in [CONTRIBUTING](../CONTRIBUTING.md).
3. Run the same entrypoint as CI (artifacts go to `dist/<package-version>/`,
   selected by exact filename so older builds cannot enter acceptance):

```sh
export IDDQUEUE_TEST_DATABASE=dedicated
uv run --locked --extra binary --extra monitoring sh scripts/check_release.sh
```

The command fails on missing DB prerequisites or any check. It runs Ruff,
unit/functional tests, strict RST/local file links, strict OpenSpec, uv lock/dependency checks,
build, LICENSE validation, clean base/monitoring wheel installs and the executable
[quickstart](quickstart.py). The gate also installs the optional FastAPI example
group and checks its lifecycle, event-loop safety and separate worker acceptance. It prints checked commit, working tree and SHA256
for artifacts. Run from a clean candidate for final evidence; a dirty tree result
must explicitly name its modifications and does not certify the parent commit.

Base wheel checks require system libpq; clean installs require index access.
uv/OpenSpec are external tools, not runtime package dependencies. PYTHON and
UV may select executable paths if normal launchers are unavailable.
Functional tests terminate sessions/crash workers; never point at a shared DB.
The quickstart uses an isolated random schema and cleans it up separately.

4. Push the verified candidate and inspect actual CI for that exact head SHA;
   all six Python/PostgreSQL jobs must succeed. Manual validation is available:

```sh
gh workflow run tests.yml --repo wa-pis/iddqueue --ref main
gh run list --repo wa-pis/iddqueue --workflow tests.yml
gh run view RUN_ID --repo wa-pis/iddqueue
gh run watch RUN_ID --repo wa-pis/iddqueue --exit-status
```

Record results in the selected OpenSpec change's evidence, without claiming a
planned workflow or queued run passed. CI failure is evidence to investigate,
not a reason to silently skip checks. Preserve user-facing changelog separately.

Evidence format:

```text
Candidate commit: full SHA; clean/dirty tree and exact modifications
Environment: Python/PostgreSQL and tool versions, dedicated DB identifier
Checks: exact commands, exit status, test counts; omitted checks and reason
CI: run URL/head SHA and each of six job URLs/results
Artifacts: wheel/sdist filenames and SHA256 from that build
Migration: upgrade steps and limitations
Publication: not performed / separately authorized action and result
```

Hashes identify a build, not an assurance that an arbitrary later build is equal.
The readiness procedure stops here. Version changes, release tags, package upload
and repository settings are separate actions, never implied by passing checks.

Published release candidate: [0.13.0rc1 notes](rc-0.13.0rc1.md).
