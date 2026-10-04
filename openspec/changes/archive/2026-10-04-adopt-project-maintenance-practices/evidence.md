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

### Этап 1 подтверждён

Исправленный commit 2c7ef9c964cc49e821ece54ddabb8076000e9d90 в main;
workflow_dispatch на ref main: https://github.com/wa-pis/iddqueue/actions/runs/37193025467.
Статус completed/success; все шесть jobs выполнили общий release check,
131 tests passed в каждом. Checked commit в логах совпадает с headSha,
working tree clean. SHA256 wheel и sdist совпали с локальными хешами выше
во всех шести jobs (прочитаны фактические логи).

| Job | Result | URL |
| --- | --- | --- |
| test (3.10, 18) | success | https://github.com/wa-pis/iddqueue/actions/runs/37193025467/job/111409031266 |
| test (3.13, 18) | success | https://github.com/wa-pis/iddqueue/actions/runs/37193025467/job/111409031442 |
| test (3.14, 18) | success | https://github.com/wa-pis/iddqueue/actions/runs/37193025467/job/111409031461 |
| test (3.14, 14) | success | https://github.com/wa-pis/iddqueue/actions/runs/37193025467/job/111409031473 |
| test (3.13, 14) | success | https://github.com/wa-pis/iddqueue/actions/runs/37193025467/job/111409031477 |
| test (3.10, 14) | success | https://github.com/wa-pis/iddqueue/actions/runs/37193025467/job/111409031536 |

make -C docs PYTHON=../.venv/bin/python check и sh -n проверены отдельно.
Недоступная БД 127.0.0.1:1 приводит к exit 1 / psycopg.OperationalError
до Ruff/tests/build. Первый failed CI сохранён как regression evidence,
не заменяет успешный повтор. Tasks 1.1–1.6 завершены; stage 2/3 остаются открыты.

### Последующий CI evidence commit выявил нестабильный тест

91a5694094213d0a752b01110f10992dfb8460cb: run
https://github.com/wa-pis/iddqueue/actions/runs/37193234339 — 5 success,
Python 3.10/PG18 failure в test_expiry_and_standard_limiters: второй add
после TTL 30 ms вернул True. Локальная контролируемая пауза 60 ms подтвердила
это корректное expiry поведение backend. Test live/expired разделены: TTL
10 seconds для live assertions, принудительное истечение timestamp через
SQL для expired assertions; такой же короткий event TTL устранён в соседнем
test_durable_events. Runtime не изменён. 1.6 повторно открыт до успешного CI
последнего исправления; stage 2 не начинался.

После исправления: targeted coordination 7 passed in 3.64s; полный release
check success (131 tests), Ruff/docs/strict OpenSpec/Poetry/build/LICENSE,
base и monitoring wheel acceptance прошли; hashes wheel/sdist прежние.
Точный test duration записан ниже после чтения полного лога.

### Завершение этапа 1 после исправления timing tests

Полный локальный повтор: 131 passed in 42.38s (дерево на 91a5694 с
исправлением coordination tests), все release checks прошли.
Commit 6d13891cdd20e1f90158e3307d18698cbe595c00 отправлен в main.
Run https://github.com/wa-pis/iddqueue/actions/runs/37193574361 — success,
шесть обязательных jobs success. Ручной dispatch уже подтверждён run
37193025467, failure isolation наблюдался в 37193234339 (5 success / 1 failure).

| Job | Result | URL |
| --- | --- | --- |
| test (3.13, 18) | success | https://github.com/wa-pis/iddqueue/actions/runs/37193574361/job/111410660603 |
| test (3.10, 18) | success | https://github.com/wa-pis/iddqueue/actions/runs/37193574361/job/111410660746 |
| test (3.14, 18) | success | https://github.com/wa-pis/iddqueue/actions/runs/37193574361/job/111410660752 |
| test (3.10, 14) | success | https://github.com/wa-pis/iddqueue/actions/runs/37193574361/job/111410660803 |
| test (3.13, 14) | success | https://github.com/wa-pis/iddqueue/actions/runs/37193574361/job/111410660817 |
| test (3.14, 14) | success | https://github.com/wa-pis/iddqueue/actions/runs/37193574361/job/111410660854 |

Tasks 1.1–1.6 завершены. Stage 2/3 открыты; sync/archive ещё не выполнялись.

## Этап 2 — docs и правила сопровождения, 2026-10-04

Переписаны index/get-started/user-guide/deployment, актуализированы API и README.
Проверено по exports, broker/results/CLI/SQL/scheduler и main specs controls,
cancellation, history, deduplication, batch, scheduler, distribution. Документы
не обещают публикацию, одну таблицу, отсутствие polling, ежедневный purge SLA
или exactly-once. Supported matrix и dependency ranges разделены; экспериментальные
расширения, CLI/JSON/SQL contracts и breaking migration описаны в SUPPORT.
CONTRIBUTING и три templates короткие; шаблоны используют GitHub blob links,
работающие и после вставки в PR/issue body. CHANGELOG Unreleased содержит
user-facing features/migration и consumer fixes, сохраняя upstream changelog
и attribution; internal CI/OpenSpec bookkeeping не включён. Release guide
содержит фактический entrypoint, prerequisites, evidence format и отделяет
готовность от tag/upload. Лицензия и runtime неизменны, dependencies не добавлены.

scripts/check_package.py --quickstart выполняет именно docs/quickstart.py
через Python -I из base wheel venv вне checkout. Пример применил init SQL,
проверил queue/coordination/deduplication/queue_control/attempts/schedules,
записал сообщение до запуска worker и получил результат 5. Worker/pool закрыты,
random quickstart schema удалена; отдельный SQL query подтвердил отсутствие
quickstart_% schemas. Monitoring profile проверен отдельно как прежде.
Отрицательный прогон с временно изменённым ожидаемым результатом 6 дал exit 1 /
AssertionError; cleanup всё равно удалил схему, исходный файл восстановлен.

Полный scripts/check_release.sh: Python 3.13.14 / dedicated PG14.20 :55432,
131 passed in 43.26s, Ruff (включая docs/quickstart.py), poetry check,
strict docs/local links, OpenSpec 18/18, build/LICENSE, wheel base/monitoring,
quickstart — success. Проверялось дерево на 4a4eff40c728e981250acdd253118220ee329ef3
с изменениями этапа; это не утверждение о чистом parent commit. После отрицательного
прогона final docs/Ruff/strict/diff checks повторно прошли.
Wheel SHA256: f63047b7f8a4bf8dff918875dfc49a2ac63a5754d2fd5d7798360036226bc294.
Sdist SHA256: 1ae829f617886104d38f3261ca33fc89dfac1a1f202c45d30ae9140b3944df3b.
CI последнего stage-1 evidence commit 4a4eff4 завершился success.
2.7 остаётся открытым до фактической проверки CI этапа 2.

### Stage 2 CI подтверждён

423ad24e0577c057a69b97cc54ef84f0c8321dbf в main; run
https://github.com/wa-pis/iddqueue/actions/runs/37196894638 — success.
В каждом job: 131 tests passed, installed base/monitoring profiles и quickstart
(шесть таблиц, enqueue, result=5, schema cleanup) success. Checked commit
в логах совпадает с head SHA; wheel/sdist hashes совпадают с локальным build.

| Job | Result | URL |
| --- | --- | --- |
| test (3.14, 14) | success | https://github.com/wa-pis/iddqueue/actions/runs/37196894638/job/111420544952 |
| test (3.14, 18) | success | https://github.com/wa-pis/iddqueue/actions/runs/37196894638/job/111420545076 |
| test (3.13, 14) | success | https://github.com/wa-pis/iddqueue/actions/runs/37196894638/job/111420545082 |
| test (3.13, 18) | success | https://github.com/wa-pis/iddqueue/actions/runs/37196894638/job/111420545111 |
| test (3.10, 18) | success | https://github.com/wa-pis/iddqueue/actions/runs/37196894638/job/111420545124 |
| test (3.10, 14) | success | https://github.com/wa-pis/iddqueue/actions/runs/37196894638/job/111420545148 |

## Requirement/scenario coverage

- Observable continuous checks: Tests matrix/manual ref, timeout/concurrency;
  failed job isolation в 37193234339, successful manual 37193025467.
- Installed distribution acceptance: check_package base/monitoring, metadata/CLI/
  seven resources; negative missing scheduler.sql и LICENSE checks этапа 1.
- Current user documentation: docs/README, check_docs; negative RST/file links;
  executable quickstart positive и wrong-result negative с cleanup.
- Compatibility/contribution: SUPPORT ranges/matrix/API/CLI/SQL/migrations,
  CONTRIBUTING/PR/issues; сверены с pyproject, exports и CLI; links checked.
- Release readiness: единый check_release, prerequisite/error failures и полный
  positive execution, user CHANGELOG, release evidence guide; tags/upload не выполнялись.

Новый main spec project-maintenance содержит те же пять требований и все
сценарии delta, Purpose сохранён; посторонние main specs не менялись.

## Завершение

project-maintenance синхронизирован (five requirements/all scenarios, no delta
headers), change перемещён в archive/2026-10-04-adopt-project-maintenance-practices.
После перемещения strict OpenSpec 18/18, docs/local links и diff checks прошли.
Roadmap/config обновлены по фактическим результатам; implementation CI 37196894638
6/6. Все 15 задач завершены; финальный commit сохраняет sync/archive/evidence.
Публикации/tag нет. Новые задачи не добавлены.
