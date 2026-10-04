# Evidence

## Этап 1 — проверки CI/поставки, 2026-10-04

Реализованы timeout 15 min, concurrency по workflow/ref, contents read,
fail-fast false, workflow_dispatch. Матрица Python 3.10/3.13/3.14 × PG 14/18
сохранена. CI использует общий scripts/check_release.sh; Poetry 2.5.1 и
OpenSpec 1.12.0 совпадают с локально проверенными инструментами.

Локальный полный запуск на Python 3.13.14 / выделенном PostgreSQL 14.20,
127.0.0.1:55432: `IDDQUEUE_TEST_DATABASE=dedicated PGHOST=127.0.0.1
PGPORT=55432 PGUSER=postgres PGDATABASE=postgres PYTHON=.venv/bin/python
sh scripts/check_release.sh` с .venv/bin и Homebrew в PATH.
Результат: 131 tests passed (47.12s), Ruff, poetry check, строгие RST/local
file links, strict OpenSpec 18/18, build, LICENSE wheel/sdist — success.
Base и monitoring установлены в отдельных временных venv вне checkout,
PYTHONPATH удалён; module path, metadata, CLI help/version, семь SQL resources,
generate_init_sql/generate_upgrade_sql и optional monitoring проверены.

Отрицательные проверки: wheel без iddqueue/scheduler.sql завершился exit 1
с FileNotFoundError; malformed RST, отсутствующие RST/Markdown file targets
подтверждены runnable test_project_checks.py; отсутствие
IDDQUEUE_TEST_DATABASE завершилось exit 2 до обращения к БД.
YAML разобран системным Ruby/Psych (YAML 1.1 представляет on как true),
проверены dispatch и шесть combinations; sh -n и git diff --check прошли.
Новые runtime/dev dependencies не добавлены. Документы не изменялись ради checker.

Проверялось рабочее дерево на основе 97154b2c0bb972f0bd711674a0a4aa9c7d0e5733,
с текущими изменениями этапа; это не проверка чистого указанного commit.
SHA256 wheel: f0e2eca968ffde5f6f7cb81b425f4a63f2ae43f4e722d5f8d249d0cdbd931654.
SHA256 sdist: faad3b5066a864f97d9415d1773743f8e967854a2b54518b4bb0f651e937ba8a.
Хеши относятся к этому локальному build; последующие сборки могут отличаться.

Фактические remote CI и workflow_dispatch ещё не выполнены; 1.1/1.6 остаются
открытыми до наблюдаемого результата. Этап документации пока не реализован.

### Фактический первый CI и исправление launcher

Commit 450bae3b0e58f3fe0511d8ba52b871dab499ebc2 отправлен в main.
Ручной run https://github.com/wa-pis/iddqueue/actions/runs/37192850689:
все шесть jobs выполнились, но завершились failure: `python -m poetry`
в project venv не находил Poetry, установленный отдельно на runner.
Исправлено на вызов Poetry executable (`POETRY`, default poetry).
Локальный повтор scripts/check_release.sh с POETRY=/tmp/iddqueue-poetry
(wrapper запускает локальный доступный Poetry module вместо сломанного
Homebrew launcher): 131 passed in 45.58s, все остальные checks success.
Проверялось дерево на 450bae3 с изменением launcher; hashes артефактов те же.
Рабочий failed run не считается успешным evidence; 1.1/1.6 ещё открыты.
