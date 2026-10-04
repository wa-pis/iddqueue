## 1. CI и проверки поставки

- [ ] 1.1 Обновить Tests workflow: workflow_dispatch, timeout, concurrency, contents read, fail-fast false; проверить YAML и фактический запуск всех шести matrix jobs, включая ручной ref.
- [x] 1.2 Добавить isolated wheel smoke для base и monitoring profiles вне checkout: imports/module path, metadata, CLI help/version, все SQL resources; проверить оба profiles и отрицательный сценарий missing resource.
- [x] 1.3 Добавить строгую проверку RST и локальных ссылок, адаптировать docs/Makefile к установленному docutils; проверить диагностируемый malformed RST и broken link на временных fixtures, не меняя user docs ради прохождения.
- [x] 1.4 Добавить общий release checks entrypoint, вызывающий существующие Ruff/tests/build/LICENSE, package и docs checks; проверить ненулевой exit при ошибке/prerequisite и успешный полный запуск с dedicated PostgreSQL.
- [x] 1.5 Интегрировать проверки в CI; выполнить poetry check/build, Ruff, tests/unit tests/func на dedicated PostgreSQL и openspec validate --all --strict; записать фактические результаты, commit и artifact hashes в evidence.
- [ ] 1.6 Зафиксировать этап отдельным commit, push в wa-pis/iddqueue main; записать URL и успешный результат каждого CI job, не считать подготовленный workflow выполненным.

## 2. Документация и правила сопровождения

- [ ] 2.1 Актуализировать docs/index/get-started/user-guide/api/deployment и README: имя/ссылки IDDQueue, реальные таблицы, API/CLI, upgrade, эксплуатация и ограничения новых возможностей; сверить с code/main specs и выполнить docs/link checks.
- [ ] 2.2 Добавить выбранный quickstart smoke из установленного wheel на dedicated PostgreSQL с cleanup; выполнить пример и подтвердить enqueue, результат и применённую SQL schema.
- [ ] 2.3 Добавить support/compatibility policy: проверенные Python/PostgreSQL, supported/experimental API, CLI/JSON/SQL contracts, breaking changes и migration guidance; сверить claims с pyproject, exports и текущей CI matrix.
- [ ] 2.4 Добавить CONTRIBUTING, короткие PR и bug/feature issue templates; проверить ссылки и наличие reproduction/expected behavior/validation без доменных security approvals соседнего проекта.
- [ ] 2.5 Добавить пользовательский CHANGELOG Unreleased и краткие правила его ведения; сохранить исторический upstream changelog, сверить новые entries с реализованными фичами, исключить internal-only bookkeeping.
- [ ] 2.6 Добавить release guide и evidence format с commit, checks, CI URLs и artifact hashes; проверить команды и явно отделить готовность от неавторизованных tag/upload/publication.
- [ ] 2.7 Выполнить полный release checks entrypoint и strict OpenSpec, обновить evidence; commit этапа отдельно, push в main и записать подтверждённый GitHub CI.

## 3. Завершение

- [ ] 3.1 Сверить все requirements/scenarios с code/docs и actual evidence; синхронизировать project-maintenance main spec и проверить openspec validate --all --strict.
- [ ] 3.2 Обновить roadmap/config по фактическим результатам, архивировать завершённый change после CI; проверить отсутствие незавершённых tasks, strict OpenSpec и чистый working tree после финального commit/push.
