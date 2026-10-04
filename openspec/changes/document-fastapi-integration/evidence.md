## Local verification

2026-10-04: Python 3.13.14, PostgreSQL 14.20 на выделенном localhost:55432,
uv 0.11.23, Dramatiq 2.2.1, Psycopg 3.3.6. FastAPI 0.142.2, HTTPX 0.28.1,
Uvicorn 0.54.0; uv.lock фиксирует example group отдельно от runtime metadata.

- `uv sync --extra binary --extra monitoring --group fastapi-example`: exit 0.
- `uv run --no-sync pytest tests/unit/test_fastapi_example.py tests/func/test_fastapi_example.py -q`: 4 passed, 3.37s.
- HTTP acceptance: явный lifespan, POST → 202/message_id → строка изолированной PostgreSQL schema; `dramatiq --use-spawn --processes=1 --threads=1 examples.fastapi.worker` → result 5; worker остановлен, pool закрыт, schema удалена.
- Дополнительный live smoke `/tmp/iddqueue-fastapi-live.py`: настоящий Uvicorn/HTTP, POST → 202 и SQL row; сервер остановлен, schema удалена. Скрипт временный; постоянный acceptance — tests/func/test_fastapi_example.py.
- Event loop: sender блокируется threading.Event, другая coroutine продолжает работу; publication не завершена до release. Ошибка → 503 без DSN; два lifespan; закрытие при registration/body errors. 3 unit tests passed повторно после добавления logging.
- `sh scripts/check_release.sh` с PG* для выделенного instance, `IDDQUEUE_TEST_DATABASE=dedicated`, UV_CACHE_DIR=/tmp/iddqueue-uv-cache, PATH=.venv/bin:/opt/homebrew/bin:…: exit 0; 147 passed, 46.74s; Ruff, uv lock/dependency check, docs, strict OpenSpec 19/19, build/LICENSE, base/monitoring wheel acceptance и installed quickstart.
- Gate проверял dirty tree поверх 20082b48632ac27baafacd9d914bdd24f9de5bf8: изменения example/tests/docs/group/CI/OpenSpec; не сертифицирует parent commit. Последующие изменения: logging проверен unit/Ruff; docs/checkbox/evidence/changelog дополнены.
- Wheel SHA256: 86b79da7083e00b0478d8b2667904940c6ea0e0774d14f903822563f7588d29d.
- Sdist SHA256: 5143622af0afa7cef009fef3d6b7d3c9f8ccede3b295b5b087296ad0c2dc7a44.
- Runtime API/DDL не изменены. AsyncConnection transactional enqueue не поддерживается; отмена HTTP не отменяет поток публикации.
- Publication/tags не выполнялись. Remote CI фиксируется только после фактического завершения.
