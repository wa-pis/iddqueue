## Decisions

Предлагаемый helper enqueue_sqlalchemy(broker, message, *, connection, delay=None, deduplication_key=None, deduplication_ttl=None) в optional module принимает SQLAlchemy Connection либо Session. SQLAlchemy extra >=2.0,<3, core import не требует его установки. Сначала поддержать synchronous PostgreSQL psycopg dialect. Native proxy driver_connection доступен по documented API; проверить реальный Psycopg Connection и active DB transaction до delegation. Engine, inactive/closed connection, async inputs и unsupported dialect/driver отклонять понятной ошибкой.

Session требует явной активной transaction и подходящего connection; не autoflush/commit, не начинать скрытую независимую transaction. SQLAlchemy logical begin может ещё не начать DB transaction — проверять реальное состояние, при отсутствии active DB transaction сообщать caller выполнить SQL/flush явно. Multi-bind Session не угадывать: caller передаёт явный Connection для нужного bind. Domain message создаётся штатным actor.message после корректного startup; adapter не делает .send и не публикует через broker pool.

Reuse enqueue_in_transaction, включая middleware/delay/dedup hooks и PostgreSQL transactional NOTIFY. Не закрывать/commit/rollback connection и не retry caller transaction. Не восстанавливать молча SQLAlchemy failed state; SQL errors caller обрабатывает rollback/savepoint. Проверить nested transaction rollback и повторное использование Connection/Session после успешной отправки. Batch helper не добавлять на первом этапе.

AsyncSession/AsyncConnection требуют отдельного change: run_sync адаптирует SQLAlchemy async I/O, но не делает произвольный synchronous Psycopg путь async-safe. Не извлекать async raw connection для этого helper.

Источники: https://docs.sqlalchemy.org/en/20/faq/connections.html и https://docs.sqlalchemy.org/en/20/orm/extensions/asyncio.html .

## Migration Plan

Optional extra и явный helper в транзакции caller; существующие PostgresBroker и Psycopg API сохраняются. Никакой schema migration.
