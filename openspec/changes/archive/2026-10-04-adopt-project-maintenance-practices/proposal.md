## Why

После реализации возможностей IDDQueue документация вне README осталась
upstream-ориентированной, а CI не проверяет установку готового пакета и docs.
Нужны понятные правила сопровождения и выпуска по полезным практикам соседнего
agent-paranoid-android, без его тяжёлых security/release процедур.

## What Changes

- Улучшить существующий CI: timeout, concurrency, fail-fast false, ручной запуск.
- Проверять wheel в отдельном окружении, imports, CLI и все SQL resources.
- Актуализировать docs: quickstart, API, эксплуатация, миграции и ссылки;
  проверять RST, локальные ссылки и исполняемые примеры.
- Ввести пользовательский Unreleased changelog без внутреннего OpenSpec журнала.
- Описать поддержку Python/PostgreSQL, стабильность API и breaking migrations.
- Добавить короткие CONTRIBUTING, PR/issue templates и единый release check.
- Подготовить простой документированный выпуск с evidence конкретного commit;
  публикация, теги и изменение GitHub settings не входят в change.

## Capabilities

### New Capabilities

- `project-maintenance`: CI, проверка установленного пакета, документация,
  contribution/support policies и проверяемая готовность релиза.

### Modified Capabilities

Нет. Существующая матрица project-distribution остаётся обязательной.

## Impact

.github/workflows/tests.yml, docs/, README, CONTRIBUTING, CHANGELOG,
.github templates, scripts/ и при необходимости dev dependencies/lock.
Runtime broker, SQL migrations и публичные сигнатуры не меняются.
Poetry, лицензия/credits и шесть Python/PostgreSQL комбинаций сохраняются.
Источник подходов: /Users/agrudin/dev/my/agent-paranoid-android; адаптация
идей, без копирования его доменных политик. Signed acceptance manifests,
Scorecard, обязательные независимые approvals, контейнерный pipeline и
автопубликация не включены. Сайт документации и смена package version не нужны.
