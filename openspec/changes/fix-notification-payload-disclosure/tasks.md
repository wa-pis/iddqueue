## 1. Regression and fix

- [x] 1.1 Добавить restricted-role regression enqueue/ACK/NACK small/large/default/custom; подтвердить denied table read и failing ID-only assertion до fix, сохранить результат evidence.
- [x] 1.2 Удалить full payload ветку всех трёх SQL sinks; проследить все pg_notify и публикацию retry/batch/dedup/scheduler; regression и existing consumer consistency tests должны pass.
- [x] 1.3 Обновить CHANGELOG и migration/README: исправление не требует DDL, all publishers/workers должны обновиться; legacy hints поддержаны, downstream full-JSON listener должен читать SQL; проверить docs/link checks.

## 2. Verification and delivery

- [x] 2.1 Запустить Ruff, poetry check, strict OpenSpec и полный tests/unit tests/func на выделенном PostgreSQL; записать реальные результаты evidence.md.
- [ ] 2.2 Создать отдельный commit реализации и push main; проверить все шесть GitHub CI jobs фактически success.
- [ ] 2.3 Синхронизировать delta spec, архивировать завершённый change и обновить roadmap/evidence; commit/push и проверить final HEAD CI, без публикации пакета.
