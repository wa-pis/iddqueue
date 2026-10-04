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
