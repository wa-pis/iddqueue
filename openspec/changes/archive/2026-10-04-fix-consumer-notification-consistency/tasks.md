## 1. Подтверждение и исправления

- [x] 1.1 Добавить failing regressions stale full payload, normal→DQ stale hint, missing ID-only hint; подтвердить failures до исправления и recorded evidence.
- [x] 1.2 Сделать durable claim с queue filter и актуальным RETURNING payload, сохранив full/ID/scan wire hints; проверить regressions, failed claim lock release и namespace isolation.
- [x] 1.3 Добавить ACK/NACK backlog и prefetch saturation regression, drain unlock_q в начале итерации; проверить lock acquisition из competing session и fast retry wakeup.
- [x] 1.4 Проверить terminal hints, cancellation/pause, delayed/retry, payload >=8000 bytes и reconnect; выполнить полный tests/unit tests/func на dedicated PostgreSQL, Ruff, poetry check и strict OpenSpec, записать actual coverage/results.

## 2. Завершение

- [x] 2.1 Обновить docs о NOTIFY hints/claim и evidence с commit/repro/test results; проверить docs соответствуют коду без новых exactly-once promises.
- [x] 2.2 Commit/push исправления отдельно в wa-pis/iddqueue main, подтвердить каждый CI job и записать run URL.
- [x] 2.3 Sync main spec, обновить roadmap/config и архивировать change после проверок; выполнить openspec validate --all --strict и проверить чистый working tree после final commit/push.
