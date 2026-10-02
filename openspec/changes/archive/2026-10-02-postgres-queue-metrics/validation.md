## Verification

Локально 2026-10-02: Python 3.13.14, PostgreSQL 14.20, Dramatiq 2.2.1,
Psycopg 3.3.6, prometheus-client 0.26.0. Выделенная БД на порту 55432.

- `pytest tests/unit tests/func -x -q`: **58 passed in 30.47s**.
- Snapshot: пустая выбранная очередь, все state counts, готовая задача
  возрастом час, future ETA в queued и consumed, reset возраста при retry enqueue.
- CLI --queue использует тот же snapshot и возвращает JSON.
- Collector зарегистрирован в отдельном registry; scrape содержит ready/counts
  с queue/state, без actor/message_id labels.
- Реальные spawn workers с отдельной очередью и стандартным Prometheus:
  HTTP scrape подтвердил обработку saver, две ошибки failing, retry и histogram.
- Wheel установлен в чистый /tmp venv с binary extra, без monitoring:
  prometheus_client отсутствует; импорт, enqueue/consume/ack/statistics проходят
  на отдельной schema/prefix. Импорт — из site-packages собранного wheel.
- EXPLAIN (ANALYZE, BUFFERS, FORMAT JSON) на отдельной схеме: 10 000 сообщений,
  четыре очереди, payload 1 KB. Все очереди: planning 0.153 ms / execution 2.852 ms;
  одна очередь: planning 0.049 ms / execution 1.081 ms. Использован sequential scan;
  полный план сохранён в explain.json. Временная схема удалена.
- `ruff check .`, `poetry check`, `poetry build`: успешно.
- Strict OpenSpec validation: успешно; требования синхронизируются перед архивом.

## Limits

Замер не является benchmark production-нагрузки. Стоимость зависит от retention,
объёма JSONB и количества очередей; стартовый scrape interval 30–60 секунд.
Consumed означает claimed/prefetched, не обязательно execution. Ready-age не
учитывает ожидание внутри worker; scheduled отдельно учитывает future ETA.
Общий snapshot удалённых очередей исчезает из scrape; выбранная пустая очередь
даёт нули. Ошибки SQL не маскируются ложным нулевым backlog.
Миграция не нужна; исторические mtime не пересчитываются.
Матрица GitHub Python/PostgreSQL ещё не запускалась удалённо.
