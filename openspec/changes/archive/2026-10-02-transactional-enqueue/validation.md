# Проверка транзакционной отправки

2026-10-02: Python 3.13.14, PostgreSQL 14.20, Dramatiq 2.2.1, Psycopg 3.3.6.

- Новый API enqueue_in_transaction разделяет запись сообщения с обычным enqueue; требует активную внешнюю транзакцию.
- 6 новых тестов: атомарный commit/rollback бизнес-записи и очереди, отсутствие преждевременного NOTIFY и уведомления после rollback, владение соединением, отклонение idle/autocommit, delays/hooks и отсутствие retry ошибки.
- Полный набор: **38 passed in 19.78s**.
- Ruff: All checks passed; poetry check: All set; wheel/sdist собраны.
- openspec validate --all --strict --no-interactive: 7 passed, 0 failed.
- git diff --check: без ошибок.

Документация: README.md, docs/api.rst, docs/changelog.rst. after_enqueue означает выполнение SQL, а не commit внешней транзакции.
