## Verification

Локальная проверка 2026-10-02: Python 3.13.14, PostgreSQL 14.20,
Dramatiq 2.2.1, Psycopg 3.3.6. Использована выделенная тестовая база.

- `pytest tests/unit tests/func -x -q`: **51 passed in 23.59s**.
- Pipeline: передача результата 6 во второй actor, итог 24, чтение обоих
  результатов; ошибка первого шага сохранена как ResultFailure,
  следующая задача отсутствует в таблице очереди.
- Group: оба порядка задержек независимых задач, get_results в порядке
  отправки, completed_count до запуска 0 и после завершения 2.
- Стандартный AsyncIO: результат корутины и сохранённое исключение.
- on_retry_exhausted: один retry, терминальная ошибка, callback с исходным
  сообщением и metadata retries=1/max_retries=1; options.retries=2.
- Actor.send_with_options с timedelta(seconds=1): время выполнения actor
  не меньше времени отправки плюс 1 секунда.
- `ruff check .`, `poetry check`, `poetry build`: успешно.
- Python-примеры нового раздела README проверены через ast.parse;
  их механизмы покрыты реальными workers в tests/func/test_composition.py.
- Strict OpenSpec validation: успешно.

## Decisions and limits

Корректное имя опции установленного Dramatiq — on_retry_exhausted,
а не on_retries_exhausted; исправлены planning artifacts.
Runtime брокера менять не потребовалось. AsyncIO включён явно в example.py.
GroupCallbacks отдельно проверен в завершённом postgres-coordination.
Actor priority применяется внутри prefetch worker; глобальный SQL priority
scheduler не заявляется. Broker остаётся синхронным, доставка at-least-once.
Матрица GitHub Python/PostgreSQL пока не запускалась удалённо.
