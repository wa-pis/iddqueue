# Project workflow

Use OpenSpec for project planning and changes. Read `openspec/config.yaml` and
relevant specs/change artifacts before implementation. Keep proposal, delta
specs, design and tasks consistent with the user's agreed scope. Update task
checkboxes after implementation and verification; record actual test coverage.
Do not treat a planned task or a prepared CI workflow as completed execution.

Baseline change: `openspec/changes/archive/2026-10-02-modernize-postgres-broker/`.
Feature roadmap and dependencies: `openspec/roadmap.md`. Before working on a
feature, select its change explicitly and read its proposal, specs, design and
tasks. Check roadmap and archived changes for completed features; unchecked
tasks are not implementation evidence.
The migration was implemented before OpenSpec adoption; its completed tasks
record existing work. GitHub setup is complete: wa-pis/iddqueue, private, main; six CI matrix jobs passed. Repository and package
names must come from the user, rather than be inferred from the upstream name.

Keep the implementation small: synchronous Psycopg 3, no ORM, session-bound
advisory locks and LISTEN/NOTIFY. Preserve the upstream license and credits.
Use a dedicated PostgreSQL instance for functional tests: the suite terminates
connections and crashes/restarts its workers.

After changes, run the relevant checks: `uv run --locked --extra binary --extra monitoring ruff check iddqueue tests/unit tests/func example.py`, `uv run --locked --extra binary --extra monitoring pytest tests/unit tests/func`
(with a prepared test database), `uv lock --check`, and `uv build` when
packaging changes. Validate OpenSpec with `openspec validate --all --strict`.

Commit each completed feature separately after its required checks pass.
Include its implementation, tests, documentation and OpenSpec artifacts in
that commit. Do not accumulate completed features in the working tree.
GitHub destination is agreed: wa-pis/iddqueue, main. Push completed, verified changes there; package publication requires a separate request.
