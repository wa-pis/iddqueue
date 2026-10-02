## 1. Подготовка исходного проекта

- [x] 1.1 Скачать Git-историю upstream, документацию, тесты, wheel и sdist 0.12.0; проверить SHA256 по PyPI и сохранить upstream remote.
- [x] 1.2 Изучить брокер, результаты, CLI и схему; проверить актуальные версии через PyPI и зафиксировать ограничения в design.md.

## 2. Миграция runtime

- [x] 2.1 Обновить зависимости до Dramatiq 2.2.1, Psycopg 3.3.6 и psycopg-pool 3.3.3 с Python ≥3.10; проверить установку окружения и poetry check.
- [x] 2.2 Перенести пул, транзакции и LISTEN/NOTIFY на Psycopg 3; проверить rollback, сохранение соединений и исходного autocommit внешнего пула тестами test_migration.py.
- [x] 2.3 Перенести Jsonb и SQL-параметры, освободить locks при закрытии потребителя; проверить requeue, большие сообщения и shutdown через функциональные тесты.
- [x] 2.4 Изолировать QueryManager экземпляров; проверить test_broker_schema_isolation.
- [x] 2.5 Исправить TTL, часовой пояс, большие результаты и миллисекундные таймауты; проверить test_result_ttl_and_timezone, test_large_blocking_result и test_subsecond_and_zero_timeout.
- [x] 2.6 Проверить ack/nack, retries, задержки, переподключение, падение и восстановление workers; выполнить tests/func/test_broker.py на выделенном PostgreSQL.

## 3. Поставка и проверки

- [x] 3.1 Обновить PEP 621 metadata, extra binary и poetry.lock; проверить poetry check и состав зависимостей wheel.
- [x] 3.2 Обновить примеры, документацию, Docker и тестовый runner; проверить отсутствие runtime-зависимостей Psycopg 2 и работоспособность нового примера в worker-тестах.
- [x] 3.3 Подготовить GitHub Actions с матрицей Python 3.10/3.13/3.14 × PostgreSQL 14/18; проверить конфигурацию .github/workflows/tests.yml, не отмечая её запуск выполненным.
- [x] 3.4 Выполнить локальную интеграционную проверку на Python 3.13.14/PostgreSQL 14.20; подтвердить 32 passed, успешный Ruff и git diff --check.
- [x] 3.5 Собрать wheel/sdist и установить wheel в отдельный каталог; проверить импорт, наличие schema.sql и ленивый пул; отдельно повторить 4 CLI-теста после финального исправления cleanup.
- [x] 3.6 Проверить init/stats/purge/recover/flush на нестандартной схеме и префиксе таблиц отдельным интеграционным сценарием; завершение подтверждается passing test.

## 4. OpenSpec

- [x] 4.1 Инициализировать OpenSpec и навыки Codex; проверить openspec/config.yaml и .agents/skills/openspec-*.
- [x] 4.2 Зафиксировать proposal, три delta specs, design, tasks и evidence локальной проверки; проверить наличие артефактов через openspec status.
- [x] 4.3 Выполнить openspec validate --all --strict --no-interactive; подтвердить отсутствие ошибок.

## 5. Новый GitHub-проект

- [x] 5.1 Получить от пользователя владельца, имя, видимость репозитория и решение об имени Python-пакета/import/CLI; записать выбранные значения в design.md перед изменениями идентичности.
- [x] 5.2 Создать новый GitHub-репозиторий и настроить origin с сохранением upstream; проверить URL репозитория и git remote -v.
- [x] 5.3 Привести метаданные, ссылки и credits к выбранной идентичности; при переименовании обновить specs, проверить poetry check, сборку и импорт установленного wheel.
- [ ] 5.4 Отправить исходники в новый репозиторий и выполнить полную GitHub-матрицу; проверить успешные результаты всех шести комбинаций в GitHub Actions.
- [ ] 5.5 После выполнения требований синхронизировать delta specs и архивировать change; проверить основные specs и openspec validate --all --strict.

## 6. Локальная идентичность IDDQueue

- [x] 6.1 Переименовать distribution/import/CLI в iddqueue; обновить активные примеры, тесты и CI, сохранив LICENSE/upstream credits и SQL/wire namespace.
- [x] 6.2 Проверить полный PostgreSQL suite, сборку, LICENSE в артефактах и установленный wheel с import/CLI iddqueue; закоммитить локально.

## 7. Регрессия retry, обнаруженная удалённым CI

- [x] 7.1 Воспроизвести детерминированно уведомление queued retry до освобождения session lock; после unlock повторно уведомить очередь, не ожидая случайного recovery scan.
- [ ] 7.2 Выполнить локальные PostgreSQL tests и полную удалённую матрицу; записать evidence, отдельный commit.
