## Context

wa-pis/iddqueue main/public, Trusted Publishing publish.yml/environment pypi уже настроен. Async single/batch feature dc6539b прошёл200localtests и CI37581161072first6/6. Security scan e0ffea74-d1ef-47b0-977b-a93c6a43bcbe завершён без findings.

## Decisions

Новая dist/0.13.0rc5, signed candidate после полного gate; проверка шести matrix jobs до publication. Signed tag указывает на точный candidate. Publisher отдельным commit pins version/candidateSHA/artifactSHA256, скачивает GitHub assets, без rebuild. Проверить GitHub readback, PyPI metadata/hashes, чистую index installation и async actor recipe вне checkout. Документы описывают RC5 доступность и caller-owned transaction, sync workers/hooks, отдельные SQLAlchemy ограничения.

## Risks / Trade-offs

PyPI version immutable: неизвестный upload outcome сначала проверить readback. Предыдущие dist/tag/assets не менять. Status completion отмечать только после фактической проверки; новая публикация авторизована текущим запросом.
