# Критическое ревью — 2026-10-04

Baseline: 97b5a90. Read-only review runtime, SQL, CLI, Results, coordination,
history, scheduler, metrics, tests и упаковки. Caveman — короткие findings;
Ponytail — простое исправление общей точки, без новых abstractions/dependencies.
Это correctness/complexity review, не полный security scan. CI/docs долги
уже покрыты adopt-project-maintenance-practices, повторно не создаются.

## Findings

- **R1 / P1 — broker.py:327–335, CONSUME_ONE.** Старый full NOTIFY исполняет
  прежние kwargs, хотя очередь хранит новый payload. Читать payload атомарного
  claim из PostgreSQL, не использовать содержимое notification как источник истины.
- **R2 / P1 — broker.py:CONSUME_ONE.** Claim по ID без queue_name: normal
  consumer принимает строку, уже перенесённую в DQ, с obsolete payload без ETA.
  Добавить expected queue predicate, skip moved row. Исправляется общей точкой R1.
- **R3 / P2 — broker.py:fetch_by_id.** ID-only hint после DELETE приводит к
  fetchone() == None и TypeError; обычный connection wrapper это не обрабатывает.
  Missing row — skip; следующий valid hint должен продолжать работу.
- **R4 / P1 — broker.py:__next__/purge_locks.** Успешный claim возвращает раньше
  drain unlock_q. Постоянный backlog удерживает завершённые session locks и
  растит unlock queue; возможны задержки retries и расход общей lock memory.
  Drain перед prefetch guard/следующим claim, оставив NOTIFY_UNLOCKED.

## Actual reproduction

Выделенный PostgreSQL 14.20, Python 3.13.14, временная schema review_<uuid>,
отдельные consumers; schema удалена и sessions закрыты в finally. Legacy full
и ID-only Notify созданы keyword arguments по реальному wire JSON. Первый
вспомогательный запуск ошибся positional order Notify и не проверил продукт;
исправленный запуск подтвердил все четыре findings:

```json
{"finding":"stale_payload","delivered":{"value":"old"},"stored":{"value":"new"}}
{"finding":"ack_lock_retained_with_backlog","locked":true,"unlock_queue_size":1}
{"finding":"deleted_notification","exception":"TypeError","text":"'NoneType' object is not subscriptable"}
{"finding":"wrong_queue_claim","delivered_queue":"delay","stored_queue":"delay.DQ","eta_delivered":null}
```

Script воспроизведения сохранён в repro.py; это review evidence, не готовый
regression suite. Полный pytest для нового change ещё не запускался и findings
пока не исправлены. В test tasks есть failing-before/passing-after requirement.

## Ponytail disposition

Основное упрощение: единый ID hint/SQL claim вместо двух источников payload и
substring parsing. Существующий session unlock/wakeup переиспользовать.
Не удалять QueueControl, namespace hashes, savepoints или dedup ради краткости:
это проверяемые контракты, не лишняя абстракция. Микро-рефакторинг без измеримой
пользы и новые зависимости не включены. Строковую экономию не измеряли.
