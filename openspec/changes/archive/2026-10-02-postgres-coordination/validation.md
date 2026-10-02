## Verification

Проверено локально 2026-10-02 на Python 3.13.14, Dramatiq 2.2.1,
Psycopg 3.3.6 и выделенном PostgreSQL 14.20 (порт 55432).

- `pytest tests/unit tests/func -x -q`: **45 passed in 19.03s**.
- 4 отдельных spawn-процесса: единственный успешный add, точные границы
  incr/decr и общая сумма окна не выше лимита.
- Повторная миграция существующей очереди сохраняет сообщение; проверена
  новая схема с префиксом и исходный init, включая таблицу координации.
- TTL, стандартные Concurrent/Bucket/WindowRateLimiter, смена окна при
  ожидании locks, durable-событие до подписки и во время ожидания,
  timeout, блокирующий Barrier с двумя ожидающими, purge.
- Реальные Dramatiq workers: группа из четырёх задач и callback;
  на момент записи callback все четыре записи задач присутствуют.
- `ruff check .`, `poetry check`, `poetry build`: успешно.
- Wheel содержит backend и coordination.sql; wheel/sdist собраны.
- `openspec validate --all --strict --no-interactive`: успешно.

## Limits

Матрица GitHub Python 3.10/3.13/3.14 × PostgreSQL 14/18 ещё не запускалась.
Повторная доставка может повторно уменьшать стандартный barrier; exactly-once
callback не заявляется. Истечение TTL занятого слота не останавливает actor.
Ожидающие занимают pool connections; очистку expired rows вызывает purge.
Мутации не ретраятся автоматически после неоднозначного разрыва соединения.
