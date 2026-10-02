# Проверка выполненной локальной миграции

Дата: 2026-10-02. Работа выполнена до принятия OpenSpec; этот документ фиксирует полученные результаты, а не новые запуски тестов.

## Среда

- macOS, Python 3.13.14.
- Dramatiq 2.2.1, Psycopg 3.3.6, psycopg-pool 3.3.3.
- Временный PostgreSQL 14.20 на 127.0.0.1:55432; после проверки остановлен.
- Upstream commit: 80b1a490d0a494925a9f8be399a11b38cee5480a; локальная ветка fork.

## Результаты

- `pytest tests/unit tests/func -x -q`: **32 passed in 19.35s**.
- После финального изменения cleanup CLI: `pytest tests/func/test_cli.py -q`: **4 passed in 0.36s**.
- `ruff check dramatiq_pg tests/unit tests/func example.py`: **All checks passed**.
- `ruff format --check dramatiq_pg tests/unit tests/func example.py`: **16 files already formatted**.
- `poetry check`: **All set**.
- `poetry build`: созданы wheel и sdist версии 0.13.0.
- Wheel установлен в отдельный каталог; подтверждены импорт из этого каталога, доступность schema.sql и создание закрытого ленивого пула.
- `git diff --check`: без ошибок.

## Связь требований с проверками

| Контракт | Проверки |
| --- | --- |
| Конкурирующие workers, ack/nack, retry, delay | tests/func/test_broker.py |
| Разрыв соединений, crash/recover | test_reconnect, test_crash, test_recover |
| Транзакции и cleanup пула | test_transaction_preserves_connection_and_rolls_back, test_external_pool_restores_autocommit_and_subscriptions |
| Освобождение locks и requeue | test_requeue_and_close_release_locks |
| Большие сообщения | test_large_message_notification |
| Результаты и ошибки задач | tests/func/test_results.py |
| TTL, часовой пояс, большие результаты, timeout | tests/func/test_migration.py |
| Независимые SQL-настройки | test_broker_schema_isolation |
| CLI стандартной схемы | tests/func/test_cli.py и ручной init тестовой базы |
| Устанавливаемая поставка | poetry build и импорт установленного wheel |

## Ещё не подтверждено

- Полная матрица Python 3.10/3.13/3.14 × PostgreSQL 14/18 в GitHub.
- Работа всех CLI-команд на нестандартной схеме и префиксе в отдельном интеграционном сценарии.
- Создание нового GitHub-репозитория и итоговая идентичность пакета.
- Публикация пакета и совместная работа старых и новых workers.

Логи локальных тестов находились в /tmp; долговременными доказательствами служат тесты в репозитории и будущие результаты CI.
