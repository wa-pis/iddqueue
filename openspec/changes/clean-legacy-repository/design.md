## Context

rg показал: nested Compose — единственный caller entrypoint.sh и единственная active Poetry команда; postgresql-conf.sh не используется; Pyright include=dramatiq_pg ссылается на отсутствующий package. Logo assets не подключены active docs. CHANGELOG symlink дублирует сохранённый docs/changelog.rst. Perf scripts указаны в docs/why.rst и не удаляются как произвольный мусор.

## Goals / Non-Goals

**Goals:** один актуальный dev workflow, отсутствие ложных setup instructions и unused assets.

**Non-Goals:** переписывание истории, удаление LICENSE/credits/OpenSpec evidence, изменение runtime, perf refactor и удаление тестов ради уменьшения repository.

## Decisions

Удалять только files с подтверждённым отсутствием callers либо obsolete replacement. Корневой Compose предоставляет dedicated PostgreSQL без init volumes: IDDQueue CLI устанавливает всю схему; tests/func/schema.sql вызывается отдельно из dev commands. Existing docs Makefile остаётся полезным wrapper docs checker. Архивные OpenSpec ссылки/команды остаются историческим evidence, а не живыми инструкциями.

## Risks / Trade-offs

- Удалённые legacy helpers могут использоваться вне repo → указать replacement в changelog/dev docs; Git history хранит файлы.
- Compose runtime недоступен → не выдавать native PostgreSQL verification за проверку Docker; статически проверить YAML и выполнить тот же init/test workflow на dedicated native PostgreSQL.
