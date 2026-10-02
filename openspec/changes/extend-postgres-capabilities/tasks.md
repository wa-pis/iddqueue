## 1. Дедупликация отправки

- [x] 1.1 Добавить namespaced dedup table/UNIQUE/TTL и idempotent migration; проверить init и upgrade существующей БД.
- [x] 1.2 Добавить API ключа/TTL для enqueue и enqueue_in_transaction; вернуть исходный ID при дубле без перезаписи payload и повторных enqueue hooks.
- [x] 1.3 Проверить concurrent producers, rollback/savepoint, expiry, payload conflict, purge до expiry и schema/prefix isolation на dedicated PostgreSQL.
- [x] 1.4 Обновить docs и evidence этапа; выполнить Ruff, полный tests/unit tests/func на выделенном PostgreSQL, poetry check, strict OpenSpec и build/license checker при изменении packaging/SQL resources.
- [x] 1.5 После проверок зафиксировать этап отдельным commit и push в wa-pis/iddqueue main; проверить успешный GitHub CI и записать ссылку, не отмечая подготовленный workflow выполненным.

## 2. Пауза и возобновление очереди

- [x] 2.1 Добавить control table/migration и pause/resume/status API/CLI для normal/DQ как одной логической очереди.
- [x] 2.2 Сериализовать pause и разрешение старта в SQL; остановить claim и prefetched execution без расходования retries; resume отправляет wakeup.
- [x] 2.3 Проверить pause/start race, prefetched и delayed сообщения, restart while paused, другие очереди и namespace isolation.
- [x] 2.4 Обновить docs и evidence этапа; выполнить Ruff, полный tests/unit tests/func на выделенном PostgreSQL, poetry check, strict OpenSpec и build/license checker при изменении packaging/SQL resources.
- [x] 2.5 После проверок зафиксировать этап отдельным commit и push в wa-pis/iddqueue main; проверить успешный GitHub CI и записать ссылку, не отмечая подготовленный workflow выполненным.

## 3. Отмена задач

- [ ] 3.1 Добавить cancelled state/migration, request flag, cancel/status CLI/API и Results cancellation exception; обновить stats/metrics.
- [ ] 3.2 Переиспользовать разрешение старта; отменять queued/delayed/prefetched до actor, предоставить cooperative check для started actor.
- [ ] 3.3 Проверить cancel/start race, repeated cancel, missing/done, Results, retry/recover/ack races и отсутствие resurrection.
- [ ] 3.4 Обновить docs и evidence этапа; выполнить Ruff, полный tests/unit tests/func на выделенном PostgreSQL, poetry check, strict OpenSpec и build/license checker при изменении packaging/SQL resources.
- [ ] 3.5 После проверок зафиксировать этап отдельным commit и push в wa-pis/iddqueue main; проверить успешный GitHub CI и записать ссылку, не отмечая подготовленный workflow выполненным.

## 4. Остальные middleware Dramatiq

- [ ] 4.1 Добавить integration scenarios AgeLimit, CPython TimeLimit, ShutdownNotifications, success/failure Callbacks и CurrentMessage.
- [ ] 4.2 Проверить состояния очереди, retry budget, Results и освобождение locks после skip/interruption; изолировать test workers/queues.
- [ ] 4.3 Документировать ограничения interrupts и контракты callbacks/CurrentMessage без собственного middleware clone.
- [ ] 4.4 Обновить docs и evidence этапа; выполнить Ruff, полный tests/unit tests/func на выделенном PostgreSQL, poetry check, strict OpenSpec и build/license checker при изменении packaging/SQL resources.
- [ ] 4.5 После проверок зафиксировать этап отдельным commit и push в wa-pis/iddqueue main; проверить успешный GitHub CI и записать ссылку, не отмечая подготовленный workflow выполненным.

## 5. История попыток

- [ ] 5.1 Добавить attempt table/migration и opt-in lifecycle middleware с отдельным attempt_id и ограниченным текстом ошибок.
- [ ] 5.2 Добавить paginated CLI history и независимый retention purge без args/kwargs по умолчанию.
- [ ] 5.3 Проверить successful/failed/retried/incomplete attempts, worker crash, isolation, pagination, retention и отсутствие writes при выключенной history.
- [ ] 5.4 Обновить docs и evidence этапа; выполнить Ruff, полный tests/unit tests/func на выделенном PostgreSQL, poetry check, strict OpenSpec и build/license checker при изменении packaging/SQL resources.
- [ ] 5.5 После проверок зафиксировать этап отдельным commit и push в wa-pis/iddqueue main; проверить успешный GitHub CI и записать ссылку, не отмечая подготовленный workflow выполненным.

## 6. Пакетная отправка

- [ ] 6.1 Добавить batch API для собственной и внешней транзакции с savepoint, общими per-message hooks, delay и dedup поддержкой.
- [ ] 6.2 Проверить all-or-nothing, caught exception во внешней транзакции, duplicates, empty/mixed queue batch, rollback и notifications after commit.
- [ ] 6.3 Измерить SQL query count и время одиночной/пакетной отправки на фиксированной выборке; записать evidence без неподтверждённых performance claims.
- [ ] 6.4 Обновить docs и evidence этапа; выполнить Ruff, полный tests/unit tests/func на выделенном PostgreSQL, poetry check, strict OpenSpec и build/license checker при изменении packaging/SQL resources.
- [ ] 6.5 После проверок зафиксировать этап отдельным commit и push в wa-pis/iddqueue main; проверить успешный GitHub CI и записать ссылку, не отмечая подготовленный workflow выполненным.

## 7. Периодический scheduler

- [ ] 7.1 Добавить interval schedule table/migration и CLI create/list/disable plus foreground scheduler с clean shutdown.
- [ ] 7.2 Отправлять due occurrences и продвигать next_run одной транзакцией с SKIP LOCKED и dedup occurrence key; PostgreSQL clock, UTC, coalesce.
- [ ] 7.3 Проверить два scheduler процесса, crash before/after commit, missed intervals, disabled schedule, paused destination и namespace isolation.
- [ ] 7.4 Обновить docs и evidence этапа; выполнить Ruff, полный tests/unit tests/func на выделенном PostgreSQL, poetry check, strict OpenSpec и build/license checker при изменении packaging/SQL resources.
- [ ] 7.5 После проверок зафиксировать этап отдельным commit и push в wa-pis/iddqueue main; проверить успешный GitHub CI и записать ссылку, не отмечая подготовленный workflow выполненным.

## 8. Завершение

- [ ] 8.1 Сверить code, docs и все delta specs с подтверждёнными сценариями; синхронизировать main specs без потери прежних требований.
- [ ] 8.2 Проверить завершение всех этапов/CI, обновить roadmap, архивировать change и выполнить openspec validate --all --strict.
