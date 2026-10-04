## Context

PostgresBroker создаёт и закрывает собственный синхронный pool; переданный pool остаётся у вызывающей стороны. Actor связывается с конкретным broker. Мотивация — proposal.md; библиотека сохраняет синхронный API.

## Goals / Non-Goals

**Goals:** воспроизводимый пример отправки из FastAPI, корректное владение ресурсами и проверка обработки задачи отдельным worker.

**Non-Goals:** async PostgreSQL backend/producer, FastAPI adapter API, HTTP API управления очередью или ожидания результатов, автоматическая инициализация схемы при запуске сервера.

## Decisions

- Общая небольшая функция регистрации actors получает explicit broker. Web lifespan создаёт broker и actors для процесса приложения; отдельный worker entry point регистрирует те же имена на собственном broker. Не создавать web pool при импорте и не переносить открытый pool между процессами. Альтернатива с глобальным actor и сменой global broker затрудняет повторный lifespan и тесты.
- В async endpoint отправлять через `await asyncio.to_thread`; создание/закрытие broker с потенциальным I/O тоже выносить из event loop. Для обычного `def` endpoint описать прямой `.send()`: FastAPI запускает такой endpoint в threadpool. Новый async API библиотеки для этого не нужен.
- Возвращать HTTP 202 и message_id только после завершения отправки. Ошибка отправки не должна превращаться в успешный ответ; пример не раскрывает DSN или текст SQL. 202 означает принятие в очередь, а не выполнение. Не использовать fire-and-forget/BackgroundTasks для надёжной публикации.
- Конфигурацию PostgreSQL брать из окружения; создание схемы — отдельная явная команда. Пример не содержит credentials. FastAPI, HTTPX для тестов и Uvicorn для запуска помещать в отдельную uv dependency group примера, подключённую в проверках; runtime dependencies остаются прежними.
- Проверить HTTP → PostgreSQL → отдельный Dramatiq worker на изолированной тестовой схеме. Проверку неблокирующей отправки делать с управляемым блокирующим sender и синхронизацией через events, чтобы подтвердить прогресс другого coroutine без хрупкого сравнения задержек. Проверять lifespan, повторный запуск и закрытие собственного pool при ошибках.
- HTTPX ASGITransport сам не запускает lifespan: тесты явно входят в lifespan context, без нового пакета lifespan-manager. Сохраняется существующая Python/PostgreSQL CI matrix.

## Risks / Trade-offs

- Отмена HTTP-запроса не отменяет уже работающий поток/commit → документировать неопределённый для клиента исход и идемпотентность обработки; не обещать exactly-once.
- Бизнес-транзакция на AsyncConnection и публикация через отдельный sync pool не атомарны → показать существующий синхронный transactional enqueue как отдельный вариант, явно исключить общую async-транзакцию.
- Каждый web/worker процесс имеет pool → указать необходимость учитывать суммарные соединения и ограничивать pool по настройкам приложения.
- Пример увеличивает dev lock → отдельная dependency group; устанавливать её только для запуска и acceptance, без framework runtime dependency.

## Migration Plan

Изменения аддитивные: пример и docs. Схема и API IDDQueue не меняются. Откат — удалить пример и его test group без миграции данных.

Источники для реализации: [FastAPI lifespan](https://fastapi.tiangolo.com/advanced/events/), [sync/async endpoints](https://fastapi.tiangolo.com/async/), [async tests и lifespan](https://fastapi.tiangolo.com/advanced/async-tests/).
