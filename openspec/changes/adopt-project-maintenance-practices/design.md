## Context

Tests workflow уже выполняет Ruff, build/LICENSE, unit/functional tests в шести
комбинациях, но не задаёт timeout/concurrency/manual dispatch и не проверяет
изолированный installed wheel. docs/index.rst сохраняет имя, ссылки и описание
одной таблицы upstream. docs/Makefile использует устаревающий rst2html.py;
Poetry dev group уже содержит docutils. Причины изменений — proposal.md.

## Goals / Non-Goals

**Goals:** один локальный release entrypoint и читаемые docs/policies,
сохранение существующих контрактов и доказательства реальных выполнений.

**Non-Goals:** runtime refactor, смена Poetry, новый docs framework/site,
coverage threshold без baseline, кастомный CI path classifier, контейнеры,
подписи/acceptance manifests, обязательные approvals и автопубликация.

## Decisions

1. Расширить существующий Tests workflow: workflow_dispatch, read-only contents,
   timeout, concurrency и fail-fast false. Не переносить classifier соседнего
   проекта: полный обязательный matrix на push/PR сохраняет project-distribution.
   Версии Actions/Poetry выбирать и проверять при apply; не копировать чужие pins.
2. Wheel smoke — чистый venv и рабочая директория вне repo; проверить __file__,
   metadata, CLI help/version и generate_init/upgrade SQL с ресурсами. Base и
   monitoring installation проверяются отдельно; binary extra даёт удобный
   functional smoke на disposable PostgreSQL. Без network-зависимых production
   сервисов. Wheel/sdist LICENSE проверка остаётся существующей.
3. Сохранить RST user docs и docutils; Markdown подходит небольшим policies.
   README — вход и ссылки; docs — подробные инструкции. Проверять внутренние
   ссылки, строгий RST и выбранный installed-package quickstart на выделенной БД.
   Внешние URL не проверять сетью на каждом CI запуске из-за нестабильности.
4. Добавить support/compatibility policy с проверенными версиями отдельно от
   широких dependency ranges. Не обещать Python 3.11/3.12 или все PG версии
   без CI; текущие шесть комбинаций остаются baseline. Public API/CLI/SQL и
   experimental поверхности перечислить явно, без нового semver обещания 1.x.
5. CONTRIBUTING и templates короткие: цель, reproduction, тесты, docs/migration.
   CHANGELOG с Unreleased и Added/Changed/Fixed/Deprecated/Removed/Migration;
   Security только для фактических исправлений, без специальных review gates.
   Исторический upstream changelog сохранить отдельно с attribution.
6. scripts/check_release.sh переиспользует проверки CI и требуемую dedicated
   DB; prerequisite проверять явно, не пропускать functional tests молча.
   Evidence — commit, окружение, commands/results, CI URL и artifact hashes.
   Release guide описывает сборку и review; tag/upload возможны только по
   отдельному запросу, workflow публикации сейчас не создаётся.

## Risks / Trade-offs

- Installed wheel может случайно импортировать checkout → отдельный cwd/venv,
  проверка пути module и отсутствие PYTHONPATH.
- Docs примеры могут обращаться к чужой БД → выделенная ephemeral test DB,
  документированные настройки и cleanup.
- Base Psycopg требует libpq → предусмотреть системную библиотеку в CI;
  optional binary profile не заменяет проверку base dependencies.
- Большой перенос документов → два последовательных этапа, сверка с реальным
  API/SQL, без неподтверждённых обещаний поддержки/автопубликации.

## Migration Plan

Сначала CI/package/docs checks, затем актуализация docs и policies; каждый
завершённый этап — отдельный commit после checks и push/CI evidence.
Изменение файлов сопровождения обратимо git revert, SQL/data migration нет.
После всех этапов sync main spec и archive; paused автоматизацию не возобновлять
без отдельного запроса пользователя.
