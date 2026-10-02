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


# Evidence — этап 3, cancellation

2026-10-03. Cancel/status API и JSON CLI; queue started/cancel_requested,
cancelled enum state, ResultCancelled, cooperative request check.
SQL row locks сериализуют start/cancel; retries и terminal updates защищают
cancelled tombstone. Stats/collector включают cancelled; purge учитывает его.

Фактически выполнено:
- Dedicated PostgreSQL 14.20/Python 3.13.14, full suite: **97 passed in 34.70s**.
- Queued/DQ cancellation, repeated cancel, prefetched gate и stale ack/nack.
- Running request, retry → cancelled, missing/done сохранение Results.
- Реальный Worker: CurrentMessage actor увидел flag и вернул cleanup result;
  второй prefetched actor не вызван.
- Results waiter получает ResultCancelled; блокирующее чтение не ждёт timeout.
- Cancel/start transaction race: cancel ждёт row lock и возвращает requested.
- Prefix isolation с тем же UUID, upgrade дважды, CLI cancel/status/missing exit.
- Ruff, poetry check, strict OpenSpec, git diff --check: success.
- Wheel/sdist build и LICENSE checker: success; cancellation.sql включён в package.
- Existing database upgrade выполнен CLI до запуска нового runtime.

Этап 3.5 завершён: https://github.com/wa-pis/iddqueue/actions/runs/37069326903,
commit 2a0a2d1. Все шесть Python 3.10/3.13/3.14 × PostgreSQL 14/18 jobs success.
Этапы 4–7 не начаты; общий change остаётся активным.


# Evidence — этап 4, стандартные middleware

2026-10-03. Runtime брокера не менялся. Добавлены пять integration tests
и shutdown_probe в example для отдельного Dramatiq CLI процесса.

Фактически выполнено:
- Dedicated PostgreSQL 14.20/Python 3.13.14: **102 passed in 41.00s**.
- AgeLimit: expired actor не вызывается, Results failure, rejected и lock released.
- TimeLimit с штатным process_boot: CPU-bound actor прерван дважды,
  max_retries=1 исчерпан, ResultFailure.orig_exc_type=TimeLimitExceeded,
  rejected и lock released.
- Callbacks: success dict и два failure callback payloads для двух попыток;
  проверены message_id, type/message, terminal state и освобождение lock.
- CurrentMessage: ID/options верны для двух последовательных задач после failure;
  hooks до/после контекста и основной поток видят None.
- Реальный CLI spawn worker: started witness → SIGTERM → cleanup witness →
  result shutdown, state done и свободный session lock.
- Первый полный прогон: 1 failed/79 passed в shutdown probe с пустым busy loop;
  handler не перехватил асинхронный Shutdown. Probe изменён на защищённый
  короткий sleep loop; отдельный сценарий 1 passed, финальный полный suite прошёл.
- Ruff, poetry check, strict OpenSpec, git diff --check: success.
- Packaging/SQL resources не изменялись; локальная сборка отдельно не запускалась.

Этап 4.5 завершён: https://github.com/wa-pis/iddqueue/actions/runs/37070389403,
commit 063b559. Все шесть Python 3.10/3.13/3.14 × PostgreSQL 14/18 jobs success,
включая build/license checker. Этапы 5–7 не начаты; общий change активен.
