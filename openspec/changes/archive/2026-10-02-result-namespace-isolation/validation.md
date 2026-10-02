## Verification

Локально 2026-10-02: Python 3.13.14, PostgreSQL 14.20, Dramatiq 2.2.1,
Psycopg 3.3.6; выделенная БД на порту 55432.

- `pytest tests/unit tests/func -x -q`: **63 passed in 33.98s**.
- Две spawn-процесса в двух конфигурациях: разные prefixes одной schema
  и разные schemas с одним prefix. В обоих случаях одинаковые queue_name и UUID.
- Дочерние процессы сначала LISTEN, затем enqueue payload 12 KB: каждый
  подтвердил ровно один fetch_by_id, свой payload и свой результат 12 KB.
- Оба процесса одновременно подтвердили claim до освобождения barrier:
  одинаковый UUID не создаёт общий advisory lock. После ack state=done в каждой
  области; Results и SQL metrics читают свои таблицы.
- Coordination: одинаковый counter создаётся в каждой области; durable event
  одной области не обнаруживается другой.
- Каналы enqueue/ack/results для двух prefixes различны; PostgreSQL LISTEN
  не получает чужой enqueue, а собственное уведомление получает.
- Unit: кириллица/кавычки, длинные queue names, limit <=63 bytes, неоднозначные
  комбинации schema/prefix, диапазон signed advisory locks, default short format.
- use_namespace_prefix_keys=True даёт понятную ValueError; false/default
  сохраняет UUID key, logical namespace не меняет идентичность.
- Текущий набор также проверяет default Results, CLI retry и transactional enqueue.
- `ruff check .`, `poetry check`, `poetry build`, strict OpenSpec validation: успешно.

## Limits

Для non-default областей и длинных default queue names изменились wire channels;
non-default message locks также изменились. Старые/новые workers нельзя смешивать:
нужно остановить и согласованно обновить producers/workers/result waiters.
Схема и сохранённые UUID не меняются. Это application storage isolation,
не механизм database permissions. Матрица GitHub ещё не запускалась удалённо.
Один запуск тестов не стартовал из-за таймаута auto-review; разрешённый повтор
успешно выполнен, последующий окончательный прогон тоже успешен.
