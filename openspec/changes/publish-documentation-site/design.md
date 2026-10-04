## Context

Agent Paranoid использует MkDocs >=1.6.1,<2 с built-in readthedocs theme и search. IDDQueue current docs смешивают RST/Markdown; GitHub Pages ещё не настроен (API 404). Existing Tests workflow выполняет полный release gate.

## Goals / Non-Goals

**Goals:** единый docs source, удобные guide/reference nav/search, strict build и автоматический Pages deploy main; проверенные UI/CLI walkthroughs.

**Non-Goals:** framework runtime deps, copy тяжёлых security policies, custom frontend/theme, изменение PyPI assets, автоматический пакетный release на каждый push.

## Decisions

Преобразовать current RST guides в Markdown одноразово и обновить live links; docs/changelog.rst сохраняется исторически и ссылка ведёт на GitHub. MkDocs отдельный uv group docs, deps не попадают в runtime. Theme/readthedocs/search как соседний проект. GitHub Actions build для PR/push/manual; deployment только main с pages:write/id-token:write в deploy job. Pages source=workflow. Без новой системы approvals.
Manual guide различает интерфейс приложения/аккаунта и локальные действия; CLI guide даёт точные команды. Existing PyPI publisher настроен; future publishing требует нового verified candidate/tag/hashes, не автоматический reupload RC. Документация указывает ограничения async/retention/idempotency.

## Risks / Trade-offs

RST conversion/ссылки могут ломать содержание → сравнение source, strict links/anchors/nav, docs checker, local render и public HTTP verify. Historical archives не переписываются. Links за docs_root ведут на GitHub; Python executable examples используются из existing source, не продублированы в site build.
