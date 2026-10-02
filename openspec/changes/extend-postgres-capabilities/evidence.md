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

Удалённый CI этапа завершён: https://github.com/wa-pis/iddqueue/actions/runs/37063065568
commit 7f39a4d, все шесть Python 3.10/3.13/3.14 × PostgreSQL 14/18 jobs success.
Этап 1.1–1.5 завершён, реализация зафиксирована отдельно.
Этапы 2–7 не реализованы. Общий change не архивируется.


# Evidence — этап 2, управление очередью

2026-10-03. Opt-in PostgresBroker(queue_control=True), pause/resume/status
broker API и JSON CLI, control.sql в init/upgrade; upgrade идемпотентен.
Pause/start gate сериализуется общей control row FOR SHARE/UPDATE.
Deferred prefetched task возвращается queued без retry/Results/terminal skip.

Фактически выполнено на dedicated PostgreSQL 14.20/Python 3.13.14:
- Полный unit/functional suite: **87 passed in 35.56s**.
- Обычная/DQ очередь: pause запрещает claim; CLI resume scan пробуждает
  потребителя и сохраняет ETA; новая broker instance видит durable pause.
- Реальный Worker: первый actor разрешён и завершается во время pause;
  второй prefetched не запускается, Results остаётся missing, retries не растут.
  Worker stop/start сохраняет pause; resume выполняет второй actor.
- Concurrent start gate/pause: pause ждёт gate commit; последующая gate запрещает старт.
- Resume до deferred ack: release повторно будит queued задачу, сообщение не теряется.
- Независимые queue и storage prefix продолжают работать.
- Gate OperationalError: SkipMessage, actor не запускается.
- Ruff, poetry check, strict OpenSpec, git diff --check: success.
- Poetry build и LICENSE checker wheel/sdist: success.

Этап 2.5 завершён: https://github.com/wa-pis/iddqueue/actions/runs/37065548460,
commit 4db00a0. Все шесть Python 3.10/3.13/3.14 × PostgreSQL 14/18 jobs success.
Этапы 3–7 ещё не начаты; общий change остаётся активным.
