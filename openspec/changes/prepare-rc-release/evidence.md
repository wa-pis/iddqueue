## Local verification

Дата подготовки: 2026-10-05 Europe/Samara. Version 0.13.0rc1.
Python 3.13.14, PostgreSQL 14.20 выделенный localhost:55432, uv 0.11.23.
Dramatiq 2.2.1, Psycopg 3.3.6, Pygments 2.21.0.

- Проверены remote tags/releases: v0.13.0rc1 отсутствует; GitHub releases отсутствуют.
- GitHub dev alert #2: open, patched Pygments 2.20.0. Locked версия обновлена 2.19.1 → 2.21.0, минимальный dev constraint >=2.20. Остальные dependency versions не изменены.
- `uv lock --upgrade-package pygments`, locked sync, CLI/metadata: exit 0, 0.13.0rc1.
- Первый gate остановлен из-за старого пустого .venv iddqueue-0.13.0.dist-info (осталась licenses, RECORD отсутствовал); metadata сохранены в /tmp/iddqueue-stale-013-dist-info. Код CLI не менялся. Проверка uv pip теперь использует выбранный project interpreter.
- Чистый UV_PROJECT_ENVIRONMENT=/tmp/iddqueue-rc-env, UV_CACHE_DIR=/tmp/iddqueue-uv-cache, PGHOST=127.0.0.1 PGPORT=55432 PGUSER=postgres PGDATABASE=postgres IDDQUEUE_TEST_DATABASE=dedicated, PATH=/tmp/iddqueue-rc-env/bin:/opt/homebrew/bin:… UV=/opt/homebrew/bin/uv `sh scripts/check_release.sh`: exit 0.
- 147 tests passed, 47.89s; Ruff, uv lock/dependency check, docs, strict OpenSpec 19/19, build/LICENSE, exact expected-version base/monitoring wheel installs и installed quickstart.
- Gate проверял dirty tree поверх dfeb82586ad5bbccbcf1dea5fd1ae3d675218abe: metadata/lock, artifact selection/interpreter/version checks, release notes/docs/OpenSpec. Это не сертификация parent commit. Candidate SHA и actual CI будут записаны после commit.
- Старый dist/iddqueue-0.13.0-py3-none-any.whl присутствовал; acceptance использовал dist/0.13.0rc1/iddqueue-0.13.0rc1-py3-none-any.whl.
- Wheel и sdist metadata version 0.13.0rc1 проверены; все семь SQL ресурсов присутствуют. FastAPI/HTTPX/Uvicorn отсутствуют в runtime Requires-Dist. LICENSE/credits сохранены.
- Wheel SHA256: 3acc297cfae2431f66bbf43393803489db9837ec888dc513dd87b8364ec1fb00.
- Sdist SHA256: a4688f1c7f79fef71ce78e1e151e7367fd0f96ee52e1010c3c3130f5ac07b5b1.
- Notes: docs/rc-0.13.0rc1.md. Tag, GitHub release, PyPI/TestPyPI и visibility changes не выполнялись.
