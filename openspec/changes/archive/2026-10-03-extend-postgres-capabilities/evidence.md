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


# Evidence — этап 5, история попыток

2026-10-03. Opt-in AttemptHistory, namespaced SQL resource/init/upgrade,
CLI history list/purge; args/kwargs/options/results не сохраняются.

Фактически выполнено:
- Dedicated PostgreSQL 14.20/Python 3.13.14: **105 passed in 44.95s**.
- Три новых integration tests: failed retry → successful, разные UUID,
  длительность, error_type и ровно 2000 символов error_text; отсутствие payload.
- CLI два cursor pages, terminal null cursor, retention старой попытки,
  сохранение новой, Results и paused queued message.
- Disabled history не пишет, тот же message UUID в другом prefix изолирован;
  identifiers с кавычками, init и повторный upgrade; invalid limit/maxage rejected.
- Реальный CLI spawn worker: incomplete → SIGKILL всей process group →
  повтор с тем же message UUID → новая successful, исходная запись неизменна.
- Первый тестовый вариант вызывал hooks вручную без регистрации actor/queue;
  заменён исполнением настоящих Workers. Опечатка pause API исправлена.
  Финальные targeted tests: 3 passed in 3.99s; полный suite прошёл.
- Ruff, poetry check, strict OpenSpec, git diff --check: success.
- Wheel/sdist build, LICENSE checker и наличие history.sql в обоих archives: success.
- Системный poetry launcher не работал из-за libintl; тот же Poetry запускался
  через рабочий .venv/bin/python -m poetry, включая poetry run pytest/Ruff.

Этап 5.5 завершён: https://github.com/wa-pis/iddqueue/actions/runs/37071887095,
commit 9843f1f. Все шесть Python 3.10/3.13/3.14 × PostgreSQL 14/18 jobs success,
включая build/LICENSE и crash test. Этапы 6–7 не начаты; общий change активен.


# Evidence — этап 6, пакетная отправка

2026-10-03. enqueue_many/enqueue_many_in_transaction, общий enqueue params,
executemany для plain batch и сохранение dedup path для mixed batches.

Фактически выполнено:
- Dedicated PostgreSQL 14.20/Python 3.13.14: **113 passed in 42.11s**.
- Восемь новых integration cases: commit/rollback с mixed queues/DQ/ETA,
  notifications отсутствуют до commit, порядок returns и before/after hooks.
- Plain SQL error и invalid dedup TTL откатывают весь пакет; внешняя transaction
  остаётся пригодной, ранняя caller запись сохраняется, dedup keys откатились.
- Повтор key внутри batch и в следующем вызове возвращает оригинал без hooks,
  mixed ordinary message публикуется; schema/prefix с кавычками.
- Empty без pool checkout; limit 1000, invalid options/count и active txn guard.
- Ruff (включая benchmark script), poetry check, strict OpenSpec,
  git diff --check: success. Packaging/SQL resources не менялись.

Измерение: scripts/benchmark_batch.py, 100 сообщений по одному и одним пакетом,
без dedup/Results, localhost dedicated PostgreSQL, один warmup и пять samples,
один pool connection. Сохраняемый скрипт чистит собственную временную schema.
Финальные samples ms: single [18.565, 18.118, 17.912, 18.251, 18.406],
batch [1.843, 2.220, 1.761, 1.779, 1.889]. Медианы **18.251 / 1.843 ms**.
Cursor enqueue calls **100 / 1**, SQL enqueue statements **100 / 100**,
transactions **100 / 1**. Instrumentation исключает пустые health commands;
BEGIN/COMMIT и wire round trips не подсчитывались. Результат одной машины,
без утверждения такой же скорости в production или для dedup batches.

Этап 6.5 завершён: https://github.com/wa-pis/iddqueue/actions/runs/37072742814,
commit 02b99cc. Все шесть Python 3.10/3.13/3.14 × PostgreSQL 14/18 jobs success,
включая функциональные batch scenarios и build/LICENSE. Этап 7 не начат;
общий change активен до scheduler и финальной синхронизации specs.


# Evidence — этап 7, interval scheduler

2026-10-03. Namespaced schedules table, init/upgrade, PostgresScheduler,
CLI schedule create/list/disable и scheduler --once/foreground.

Фактически выполнено:
- Dedicated PostgreSQL 14.20/Python 3.13.14: **120 passed in 49.37s**.
- Seven targeted scenarios: 7 passed in 1.22s перед итоговым full suite.
- Два отдельных Python scheduler процесса стартуют по общему barrier:
  один occurrence, одна queue row и dedup key, следующий tick пустой.
- SIGKILL после enqueue до outer commit: competing tick SKIP LOCKED,
  uncommitted queue не видна; после crash следующий tick публикует без потери.
- SIGKILL после commit: queued/next_run сохраняются, повторный tick пустой.
- Coalesce пропуска 95 секунд при interval 10 секунд: ровно одна задача,
  next_run сдвинут на 100 секунд исходной сетки; non-UTC start_at/list UTC.
- Disable повторяемый/missing, старые queued сохраняются; disabled due не публикуется.
- Paused destination: actor не вызван, после resume normal Results done.
- Namespaced quoted identifiers, одно имя в разных prefix независимо,
  init/двойной upgrade; invalid interval/timezone/name/tick limit rejected.
- CLI JSON template/list без payload, foreground SIGTERM exit 0, --once,
  disable, invalid timezone/JSON container не создают schedules.
- Ruff, poetry check, strict OpenSpec, git diff --check: success.
- Wheel/sdist build, LICENSE checker, scheduler.sql в обоих archives: success.

Этап 7.5 завершён: https://github.com/wa-pis/iddqueue/actions/runs/37073608454,
commit 7f3ea69. Все шесть Python 3.10/3.13/3.14 × PostgreSQL 14/18 jobs success,
включая scheduler process/crash scenarios и build/LICENSE.

# Завершение общего change

Все семь этапов реализованы отдельными feature commits с full local suite и
фактической успешной CI matrix; PyPI publication не выполнялась. Шесть новых
main specs созданы, remaining middleware requirement добавлен с сохранением
прежних pipelines/groups/AsyncIO/retry exhaustion/timedelta requirements.
Все семь delta bodies сверены с main specs; strict OpenSpec: 17 passed.
Change архивирован 2026-10-03 после CI; roadmap/config отражают завершение.
