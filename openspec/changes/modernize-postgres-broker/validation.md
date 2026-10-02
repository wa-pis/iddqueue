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


## Custom CLI verification — 2026-10-02

Задача 3.6 завершена отдельным passing integration scenario:
`tests/func/test_cli.py::test_custom_schema_maintenance`.

- CLI init создаёт отдельные schema/prefix с кавычками в identifiers.
- stats подтверждает по одному queued/consumed/done/rejected сообщению.
- recover --minage '1 hour' возвращает только выбранный consumed в queued.
- purge --maxage '1 hour' удаляет два старых done/rejected сообщения.
- flush удаляет два queued; финальный stats возвращает четыре нуля.
- Сообщение consumed в контрольной схеме переживает все команды без изменений.
- Тестовые схемы удаляются в finally; default область не затрагивается сценарием.

Полный прогон на выделенном PostgreSQL 14.20 и Python 3.13.14:
**64 passed in 32.51s**. Ruff, poetry check/build и strict OpenSpec validation
успешны; исправления runtime не потребовались.

Все независимые локальные задачи baseline завершены. GitHub owner и
visibility ещё ожидают ответа пользователя. Удалённая
матрица и публикация не заявляются выполненными; change не архивируется.


## IDDQueue — 2026-10-02

Имя пользователя применено: distribution/import/CLI/repository — iddqueue.
Активные код, документация, tests и CI переименованы; upstream ссылки,
LICENSE и авторство сохранены. SQL schema/таблицы, каналы и locks не менялись.
Prometheus families переименованы в iddqueue_queue_*; README описывает миграцию.

Фактически выполнено на Python 3.13.14 и выделенном PostgreSQL 14.20:
- Полный tests/unit tests/func: **64 passed in 33.38s**.
- Ruff, poetry check, git diff --check и strict OpenSpec: успешны.
- Poetry build: iddqueue-0.13.0 wheel и sdist; check_license.py проверил оба.
- Wheel установлен в /tmp/iddqueue-identity-smoke; из /tmp проверены
  импорт из site-packages, metadata version 0.13.0, оба SQL resources,
  lazy closed pool и CLI iddqueue --version (0.13.0).

Baseline остаётся активным: owner/visibility/origin/push и удалённая матрица
не выполнены. Публикация в PyPI не выполнялась.

## GitHub и retry race — 2026-10-02

Пользователь предоставил https://github.com/wa-pis/iddqueue; API подтвердил
PRIVATE и пустой репозиторий. Origin настроен через существующий SSH-доступ
wa-pis; upstream сохранён. История отправлена в main, default branch main.
HTTPS OAuth не имел workflow scope; SSH push успешно принят.
Метаданные Repository/Issues обновлены; poetry check/build и license checker прошли.

Run https://github.com/wa-pis/iddqueue/actions/runs/37054101038:
5/6 jobs success; Python 3.14/PostgreSQL 18 — ResultTimeout в retry.
Детерминированный test_retry_wakes_consumer_after_old_lock_release до fix:
1 failed (retried is None). После fix полный suite: **65 passed in 33.62s**
на Python 3.13.14/PostgreSQL 14.20. Ruff и strict OpenSpec прошли.
Release очереди повторно уведомляет queued запись после старого session lock.
Удалённая повторная матрица ещё ожидается; baseline пока не архивирован.

Run 37054623793: Python 3.14/PostgreSQL 14 success; Python 3.10/PostgreSQL 14
упал в legacy test_recover, остальные отменены fail-fast. Test_recover
изолирован от живых workers собственной схемой. После изменения полный suite:
**65 passed in 32.45s**, Ruff/poetry check/strict OpenSpec успешны.
