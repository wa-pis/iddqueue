# Проверки перехода на uv

## Configuration

uv 0.11.23 локально и pinned CI; native uv_build >=0.11.23,<0.12,
root module iddqueue, explicit license-files LICENSE. Dev dependencies PEP 735.
uv.lock создан с временными constraints из poetry.lock, constraints удалены,
повторный uv lock сохранил все версии. Сравнение name/version: отличий нет;
добавлен только editable project iddqueue. Pygments остаётся 2.19.1,
известный low advisory не объявляется исправленным этим tooling change.
Документация: https://docs.astral.sh/uv/concepts/build-backend/,
https://docs.astral.sh/uv/guides/integration/github/.

## Results

- uv lock --check: passed.
- Clean UV_PROJECT_ENVIRONMENT=/tmp/iddqueue-uv-clean sync --locked
  --extra binary --extra monitoring --python .venv/bin/python: passed,
  Python 3.13.14, dev group + monitoring + binary установлены без Poetry.
- uv build: wheel/sdist passed; check_license.py оба formats passed;
  installed editable CLI --version: 0.13.0.
- Stale metadata в /tmp/iddqueue-uv-stale (tenacity>=9.1.3):
  uv lock --check exit 1, needs update; исходный lock не изменён.
- Full release gate на dedicated PG14.20 127.0.0.1:55432: exit 0; 143 tests passed in 43.39s, Ruff/docs/lock/dependency checks, OpenSpec 19/19, build/LICENSE, installed-wheel base/monitoring (7 SQL resources), quickstart actor result=5 и cleanup passed.
- Tests CI b75ed80: https://github.com/wa-pis/iddqueue/actions/runs/37228008729 — success, все шесть jobs success. Dependency Graph 37228013893 отдельно success, не заменяет Tests matrix. Публикация не выполнялась.

SHA256 wheel: 97619dac6940dd21bde6fdaeefface98b445f1a8c567121a3a9a3fec74676359.
SHA256 sdist: 9aa3a7f8516718f80c59c8baf4dd1ca80fefee7863649b3ddf62ec5454f85e84.
rg case-insensitive Poetry по актуальным config/docs/gate: совпадений нет;
исторические OpenSpec архивы сохранены. Default .venv также синхронизирован uv.
