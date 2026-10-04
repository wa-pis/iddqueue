# Проверки

## Upstream baseline

Официальный sdist dramatiq_pg-0.12.0.tar.gz, SHA256
828245fcf3700f6098ec1bff9eb13e50acff69d9c490ceeec5b69ee75d0f9fb1.
PyPI: https://pypi.org/project/dramatiq-pg/0.12.0/.
Скачан в /tmp/iddqueue-upstream-012; metadata: Python ^3.6,
Dramatiq ^1.5, Tenacity ^8; broker/utils/results используют Psycopg 2.
Исходный broker API содержит обычный enqueue(delay), базовые lifecycle/maintenance;
в sdist отсутствуют coordination/control/cancellation/history/dedup/scheduler/metrics
backend-модули. Upstream уже имеет schema/prefix, JSONB/results/delay/recovery.
IDDQueue расширения подтверждены соответствующими модулями и tests/func;
middleware/composition предоставлены Dramatiq, здесь проверена совместимость.
Никакое отсутствие CI upstream или общее превосходство по скорости не заявлено.
LICENSE/credits не изменены.

## Локальные результаты

- .venv/bin/python scripts/check_docs.py — passed, включая migration.md и index.rst.
- .venv/bin/python -m poetry check — passed.
- .venv/bin/ruff check iddqueue tests/unit tests/func example.py — passed.
- openspec validate --all --strict — 19/19 passed.
- /tmp/iddqueue-migration-rehearsal.py на выделенном PostgreSQL 14.20,
  127.0.0.1:55432, postgres: исходная DDL 0.12.0 (только удалён obsolete
  WITHOUT OIDS), случайная schema migration_<uuid>, три synthetic rows
  queued/rejected/done+result; pg_dump, CLI upgrade, точное равенство rows;
  consumer claim/ACK, result read, CLI retry; DROP только fixture schema,
  pg_restore, точное восстановление исходных rows. PASS.
- Rehearsal использует исходную DDL и JSON fixtures, не запускает старый
  Dramatiq 1.x worker; пользовательские middleware/encoders требуют своей rehearsal.
- Первые попытки: pg_ctl без -o запустил порт 5432; остановлен и исправлен
  на 55432. Неверная роль agrudin заменена тестовой postgres. Первый full run
  без venv PATH: 17 failed/19 errors из-за отсутствия CLI/worker executable;
  повторный запуск использует venv PATH. Эти попытки не считаются passing.
- Полный повторный tests/unit tests/func: 131 passed in 45.38s.
