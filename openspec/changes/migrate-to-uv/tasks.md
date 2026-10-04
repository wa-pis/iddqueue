## 1. Environment and package

- [x] 1.1 Перенести dev group и build backend на uv, создать uv.lock и убрать Poetry config/lock; проверить uv lock --check и зафиксировать различия resolved versions.
- [x] 1.2 Выполнить clean locked sync binary/monitoring с dev group; проверить import/CLI и сборку wheel/sdist, все семь SQL resources и LICENSE через существующие acceptance scripts.

## 2. Workflow and documentation

- [x] 2.1 Перевести check_release.sh и шесть CI jobs на pinned uv/locked sync; проверить stale-lock failure и отсутствие зависимостей от Poetry в активном gate.
- [x] 2.2 Обновить README/docs/CONTRIBUTING/AGENTS и config на uv-команды; docs checker и rg должны подтвердить отсутствие актуальных Poetry инструкций вне исторических архивов/evidence.

## 3. Verification and delivery

- [x] 3.1 Выполнить полный release gate на выделенном PostgreSQL: tests/unit tests/func, Ruff, docs, strict OpenSpec, lock check, build/LICENSE и base/monitoring installed-wheel/quickstart; записать фактические результаты evidence.
- [ ] 3.2 Создать отдельный commit перехода, push main и проверить все шесть CI jobs success.
- [ ] 3.3 Синхронизировать main spec, архивировать change, обновить roadmap/evidence, commit/push и проверить final HEAD CI; ничего не публиковать.
