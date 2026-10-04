## 1. Documentation

- [x] 1.1 Добавить заметный upstream attribution в README; проверить ссылки GitLab/PyPI и неизменность LICENSE/credits.
- [x] 1.2 Сверить каждую строку таблицы с исходниками dramatiq-pg 0.12.0 и IDDQueue; сохранить ссылки/версию baseline и фактические evidence, не маркировать middleware Dramatiq как собственную реализацию.
- [x] 1.3 Добавить таблицу README и docs/migration.md со ссылкой из docs/index.rst; проверить последовательность остановки/upgrade/restart/rollback, pool/import/CLI/namespace/metrics, отсутствие разрушительных команд и неподтверждённых security/exactly-once/performance обещаний.

## 2. Verification and delivery

- [x] 2.1 Выполнить доступные docs/link checks, Ruff, poetry check и openspec validate --all --strict; записать команды и фактические результаты в evidence.md.
- [x] 2.2 Проверить описанные команды миграции на выделенном PostgreSQL с изолированными fixture-данными из upstream, затем tests/unit tests/func; доказать сохранность queued tasks/results и корректный rollback, ограничения отразить в инструкции.
- [x] 2.3 После проверок архивировать docs-only change, обновить roadmap, отдельным commit отправить в wa-pis/iddqueue main и проверить фактический CI; публикацию не выполнять.
