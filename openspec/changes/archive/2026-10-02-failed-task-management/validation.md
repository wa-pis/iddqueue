## Verification

Проверено локально 2026-10-02 на Python 3.13.14, PostgreSQL 14.20,
Dramatiq 2.2.1 и Psycopg 3.3.6; выделенная тестовая БД на порту 55432.

- `pytest tests/unit tests/func -x -q`: **56 passed in 27.45s**.
- Реальные workers: ошибка первого attempt сохранена при промежуточном
  retry, rejected после второго attempt содержит тип/текст/UTC time/attempt.
- Успешный автоматический retry удаляет последнюю ошибку, сохраняя retries.
- Исправление зависимости и CLI retry возвращают тот же message_id к
  успешному выполнению; старая ошибка результата очищена, цикл retries сброшен.
- CLI list: выборка 105 задач, страницы 100+5, UUID cursor, фильтры queue/actor.
  show/list не раскрывают args/traceback; show --payload раскрывает явно.
- Две конкурентные subprocess-команды retry: только одна успешна;
  получено транзакционное NOTIFY с ID задачи.
- consumed/queued/missing и удерживаемый worker-lock отвергают retry.
  После освобождения lock retry сбрасывает options и result/result_ttl.
- CLI работает с отдельными schema/prefix; лимит страницы 0 отвергается.
- `ruff check .`, `poetry check`, `poetry build`: успешно.
- Strict OpenSpec validation: успешно; main spec синхронизируется перед архивом.

## Limits

Миграция не требуется: metadata хранится в существующем JSONB сообщения.
Старые строки могут не иметь diagnostics; сообщение ошибки ограничено 2000
символами, история не хранится. Текст ошибки может содержать значения приложения.
После NACK worker может ещё удерживать advisory lock; команда в этот момент
отказывает, и её можно повторить после освобождения. UUID-pagination не является
snapshot при конкурентных изменениях. Повтор требует идемпотентности и не
сбрасывает прежние side effects/барьеры. Матрица GitHub ещё не запускалась удалённо.
