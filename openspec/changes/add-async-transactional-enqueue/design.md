## Context

См. proposal.md. Текущий broker использует синхронные cursor.execute/executemany, общие _prepare_enqueue/_enqueue_params и ENQUEUE SQL. Deduplication выполняет несколько SQL операций под savepoint; batch также использует savepoint. Psycopg уже установлен и предоставляет AsyncConnection/AsyncCursor; изменение не требует новой схемы или async pool.

## Goals / Non-Goals

**Goals:** узкий async вход для транзакции приложения с одинаковыми SQL/serialization правилами и проверяемой атомарностью.

**Non-Goals:** перевод broker/consumer/backend на async, coroutine middleware, AsyncSession/SQLAlchemy AsyncConnection, asyncpg, управление DSN/pool приложения и изменение actor.send.

## Decisions

1. Отдельные async методы на PostgresBroker: enqueue_in_transaction_async(message, *, connection, delay=None, deduplication_key=None, deduplication_ttl=None) и enqueue_many_in_transaction_async(messages, *, connection, options=None). Sync метод не возвращает условно coroutine; существующие callers остаются совместимы.
2. Проверять AsyncConnection и INTRANS до подготовки/SQL, без автоматического BEGIN и pool fallback. Документировать требование той же БД и schema/prefix брокера: чужое соединение не перенаправляется по broker DSN.
3. Переиспользовать ENQUEUE SQL, подготовку Message, параметры, batch validation и минимальные общие dedup SQL/validation helpers. Await нужен только в async I/O пути; не вводить универсальный sync/async executor, asyncio.run, thread bridge или новый abstraction layer. Небольшие async orchestration helpers допустимы вместо сложной унификации.
4. Async cursor context и await execute/fetchone/executemany; async connection.transaction() внутри уже активной транзакции создаёт savepoint для dedup/batch. Одиночная обычная публикация остаётся одним SQL statement. Commit/rollback внешней транзакции принадлежат caller.
5. Не ловить CancelledError ради retry/успешного результата. Cleanup savepoint поручить штатному Psycopg context manager; проверять реальную отмену заблокированного SQL на выделенном PostgreSQL с ограниченным временем ожидания. Соединение после ошибки простого SQL может требовать caller rollback; не обещать автоматическое восстановление внешней транзакции.
6. Enqueue hooks остаются синхронными, на текущем event loop и с тем же порядком, что sync путь. Пользовательские hooks могут блокировать loop; async публикация гарантирует async DB I/O, а не неблокирующий произвольный middleware. after_enqueue не означает внешний commit. Async SQLAlchemy adapter остаётся отдельно неподдерживаемым.

## Risks / Trade-offs

- Расхождение sync/async дедупликации → общие SQL/validation и парные functional сценарии, без переписывания рабочего sync пути.
- Отмена после успешного await, но перед commit → внешняя transaction context определяет rollback; нельзя обещать exactly-once при неизвестном исходе commit.
- Flaky отмена и проверка NOTIFY → управляемая блокировка/маркер начала SQL, bounded ожидания и отдельное observer соединение вместо случайных sleep.
- Частично вызванные hooks при batch rollback → документация сохраняет существующий контракт hooks; проверка SQL атомарности отдельно от hooks.

## Migration Plan

Аддитивный API после RC4, без DDL. Обновить текущую документацию, явно указав отсутствие методов в опубликованном RC4; исторические release notes сохраняются. Пример использует обычный Domain/native Message и caller AsyncConnection, без привязки к FastAPI. Rollback внедрения — возвращение caller к sync транзакции в потоке; публикация пакета в этот change не входит.
