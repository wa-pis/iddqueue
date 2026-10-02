# Evidence — этап 1, дедупликация

2026-10-03. Реализованы deduplication_key/deduplication_ttl в broker enqueue
и enqueue_in_transaction, namespaced deduplication.sql, generate_upgrade_sql
и CLI upgrade. Без ключа прежний путь enqueue сохранён.

Фактически выполнено:
- Python 3.13.14/PostgreSQL 14.20, выделенная БД port 55432.
- Полный tests/unit tests/func: **80 passed in 33.83s**.
- Concurrent producers с Barrier и двумя соединениями: одна строка, один ID,
  исходный payload/ETA, единственная пара hooks.
- Проверены expiry, разные logical queues/prefix, quoted schema/prefix,
  возврат исходного Message после удаления queue row.
- Outer rollback и caught exception после INSERT: savepoint удаляет key/task.
- NOTIFY до outer commit отсутствует, после commit один; duplicate без NOTIFY.
- Upgrade дважды сохраняет queue; CLI upgrade выполнен на существующей БД.
- Некорректные key/TTL отклоняются до write.
- Ruff, poetry check, strict OpenSpec, git diff --check: success.
- Poetry wheel/sdist build, LICENSE checker: success; deduplication.sql есть в wheel.

Удалённый CI этапа ещё ожидается; 1.5 пока не завершён.
Этапы 2–7 не реализованы. Общий change не архивируется.
