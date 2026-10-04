# Evidence

2026-10-05: MkDocs 1.6.1/readthedocs/search, docs dependency group locked; current RST guides converted to Markdown, historical changelog retained. Strict MkDocs build, source docs checker, Ruff, uv lock --check and strict OpenSpec (19/19) passed.

Full local tests: 147 passed in 49.24s, Python 3.13.14 / dedicated PostgreSQL 14.20 localhost:55432. First attempted run lacked a running PostgreSQL; server started with sandbox escalation, complete suite rerun passed.

Build in /tmp/iddqueue-docsite-build succeeded; wheel/sdist LICENSE verified. Published RC assets remain immutable. Exact walkthrough actor and producer executed using clean installed PyPI RC, separate Dramatiq worker and temporary database; result 5.

GitHub Pages configured build_type=workflow, public URL https://wa-pis.github.io/iddqueue/. Remote build/deploy/Tests verification pending. Docker Compose runtime was not checked locally (plugin unavailable); optional service matches repository configuration.
