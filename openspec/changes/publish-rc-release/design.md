## Context

Candidate 4e808632f920390100658b091bac2ab97a55eb2a, 147 tests, CI 6/6. Пользователь отдельно разрешил публикацию на GitHub и PyPI. Репозиторий PUBLIC проверен через gh.

## Goals / Non-Goals

**Goals:** выпуск точных проверенных файлов; подтверждённые remote results.

**Non-Goals:** пересборка/смена версии, раскрытие credentials, изменение runtime.

## Decisions

GitHub prerelease создаётся на точном candidate SHA; assets сверяются с SHA256SUMS. PyPI получает те же wheel/sdist. Credentials не принимаются в сообщениях; дальнейшая аутентификация требует настройки пользователем (предпочтительно PyPI Trusted Publishing). Пока credentials отсутствуют, PyPI task остаётся незавершённой.

## Risks / Trade-offs

- PyPI immutable version → отправлять только проверенные файлы.
- Отсутствие credentials → не считать upload выполненным; сохранить фактическую ошибку и запросить настройку доступа.

## Trusted Publishing

Пользователь разрешил настройку. Workflow publish.yml запускается вручную на main, environment=pypi, id-token:write только в publish job. Скачать существующие GitHub assets и сравнить с фиксированными SHA256 проверенного кандидата; не пересобирать, не выполнять package code. Это workflow первого RC, без автоматического запуска на каждом push и без универсального release framework. uv publish --trusted-publishing always требует OIDC и не переключается на token fallback.

PyPI pending publisher: project iddqueue, owner wa-pis, repository iddqueue, workflow publish.yml, environment pypi. Создание pending publisher в аккаунте пользователя ещё не подтверждено. Workflow запускать после настройки; фактический upload остаётся task 1.3.
