## 1. RC metadata и notes

- [x] 1.1 Проверить отсутствие конфликтующего 0.13.0rc1 tag/release, установить package version 0.13.0rc1 и обновить uv.lock без общего dependency upgrade; проверить uv lock --check и installed metadata/CLI version.
- [x] 1.2 Повторно проверить dev Pygments advisory #2 и обновить только Pygments до исправленной версии; проверить lock diff, docs checker и actual advisory status после push, записать evidence.
- [x] 1.3 Подготовить CHANGELOG section и release notes 0.13.0rc1 с migration/rollback, ограничениями и RC install instructions; проверить docs/local links, согласованность версии и сохранение LICENSE/credits.

## 2. Артефакты и release gate

- [x] 2.1 Обеспечить точный выбор RC artifacts в отдельном build directory без старых dist glob; проверить release gate в присутствии старого 0.13.0 wheel и убедиться, что acceptance использует 0.13.0rc1.
- [x] 2.2 Запустить полный gate на выделенном PostgreSQL: unit/func/FastAPI, Ruff, uv lock/dependency check, docs, strict OpenSpec, wheel/sdist/LICENSE, base/monitoring installed acceptance и quickstart; записать actual commands, counts, versions и exit status.
- [x] 2.3 Проверить wheel/sdist version 0.13.0rc1, SQL resources и runtime metadata без example dependencies; записать SHA256 и candidate SHA в evidence.

## 3. Кандидат и завершение подготовки

- [x] 3.1 Сделать отдельный commit/push RC preparation в wa-pis/iddqueue main, проверить clean tree и actual Tests CI 6/6 для точного SHA; записать URLs/results.
- [ ] 3.2 После подтверждения проверок архивировать change, обновить roadmap/evidence и выполнить strict OpenSpec; commit/push и проверить archive CI отдельно.
- [ ] 3.3 Передать пользователю подготовленную версию, candidate SHA, paths/checksums и release notes; явно указать, что tag/GitHub release/PyPI/TestPyPI ещё не выполнены и требуют отдельного запроса с каналом.
