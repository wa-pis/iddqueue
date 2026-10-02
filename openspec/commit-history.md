# История локальных этапов

Накопленные изменения разложены 2026-10-02 на последовательные коммиты
миграции и четырёх завершённых возможностей. Каждый самостоятельный
снимок проверен на выделенном PostgreSQL 14.20, Python 3.13.14.

| Коммит | Этап | PostgreSQL-тесты |
| --- | --- | --- |
| 9cfc050 | build: migrate to Psycopg 3 and Dramatiq 2 | 32 passed in 22.47s |
| 8269ec4 | feat: add transactional task publishing | 38 passed in 22.83s |
| e738fb9 | feat: add PostgreSQL coordination backend | 45 passed in 19.96s |
| d4bc60c | test: verify Dramatiq composition and middleware | 51 passed in 21.62s |
| 047ed1b | feat: inspect and retry failed tasks | 56 passed in 27.41s |

Каждый этап прошёл Ruff, strict OpenSpec validation, poetry check и
сборку wheel/sdist. В коммит фичи включены её тесты, документация,
синхронизированные specs и архив change. Для ранних этапов будущие
features оставлены как планы с незавершёнными tasks. Исходная история
upstream сохранена; рабочие файлы в процессе разбиения не менялись.

Коммиты локальные. GitHub CI и публикация не выполнялись. Следующие
фичи коммитятся отдельно после необходимых проверок (см. AGENTS.md).
