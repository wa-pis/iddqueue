## 1. Пример и документация

- [x] 1.1 Добавить минимальную uv dependency group примера (FastAPI, HTTPX, Uvicorn); проверить locked sync и отсутствие новых runtime dependencies в metadata.
- [x] 1.2 Добавить web app с lifespan, explicit actors, async отправкой через to_thread и отдельный worker entry point; проверить запуск обоих процессов по документированным командам.
- [x] 1.3 Описать setup схемы, конфигурацию, def/async def endpoints, 202/message_id, shutdown, pool на процесс, идемпотентность и ограничение AsyncConnection; добавить ссылки из README/docs index и проверить docs checker.

## 2. Acceptance

- [x] 2.1 Проверить HTTP 202 → реальная строка очереди → выполнение отдельным Dramatiq worker на выделенном PostgreSQL с изолированной схемой; записать фактический результат и cleanup.
- [x] 2.2 Проверить прогресс event loop при управляемой блокирующей отправке, отсутствие ложного 202 при ошибке и lifecycle/повторный lifespan/закрытие pool при ошибках; тесты используют явный lifespan и ограниченные ожидания, без проверки скорости по таймингам.
- [x] 2.3 Подключить acceptance и dependency group к существующему CI/release gate; проверить, что пример действительно исполняется и Ruff проверяет новые Python-файлы.

## 3. Завершение

- [x] 3.1 Выполнить полный tests/unit tests/func на выделенном PostgreSQL, Ruff, uv lock --check, docs checks, strict OpenSpec и build/installed metadata при изменении packaging; записать версии, команды и результаты в evidence.md.
- [ ] 3.2 Commit/push завершённого change в wa-pis/iddqueue main; проверить фактический GitHub CI, записать ссылку/результат в evidence и обновить roadmap.
- [ ] 3.3 Архивировать завершённый docs-only change после проверок; проверить strict OpenSpec, commit/push архива и фактический CI. Delta specs отсутствуют по skip_specs.
