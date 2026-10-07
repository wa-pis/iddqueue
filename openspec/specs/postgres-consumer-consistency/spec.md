# postgres-consumer-consistency Specification

## Purpose

Обеспечить исполнение актуальной версии сообщения из правильной очереди,
без падений на устаревших уведомлениях и накопления завершённых session locks.

## Requirements

### Requirement: Authoritative queue claim

Consumer SHALL исполнять payload, сохранённый в PostgreSQL на момент успешного
claim, только из своей queue_name. NOTIFY SHALL служить hint; прежние полные
и ID-only уведомления MUST оставаться допустимыми.

#### Scenario: Stale payload
- **WHEN** сообщение обновлено с тем же ID, а consumer получает старое полное уведомление
- **THEN** consumer использует актуальные actor/kwargs/options из успешно claimed строки

#### Scenario: Message moved to delay queue
- **WHEN** ID перенесён из normal в DQ, а normal consumer получает прежнее уведомление
- **THEN** normal consumer не claims строку; DQ consumer сохраняет актуальную ETA и delay semantics

### Requirement: Obsolete notification tolerance

Уведомления для missing либо неподходящих queue/state messages SHALL пропускаться
без падения consumer и без исполнения отсутствующей или терминальной задачи.

#### Scenario: Deleted large message
- **WHEN** после ID-only NOTIFY сообщение удалено flush/purge до чтения consumer
- **THEN** hint пропущен, consumer продолжает обработку следующей действительной задачи

#### Scenario: Terminal message hint
- **WHEN** consumer получает повторное уведомление done/rejected/cancelled задачи
- **THEN** задача не выполняется снова из-за этого hint и лишний lock не остаётся удержанным

### Requirement: Prompt completed lock release

Завершённые ACK/NACK session locks SHALL освобождаться на следующей итерации
consumer независимо от наличия pending notifications и prefetch saturation.
Retry wakeup после unlock SHALL сохраняться.

#### Scenario: Continuous backlog
- **WHEN** одна задача ACK/NACK завершена и следующая queued задача немедленно доступна
- **THEN** session lock завершённой попытки освобождён до claim следующей задачи

#### Scenario: Fast retry
- **WHEN** retry опубликован до освобождения lock предыдущей попытки
- **THEN** unlock отправляет wakeup, retry доступен без ожидания случайного recovery scan

### Requirement: Minimal outgoing task notifications

Broker SHALL отправлять в уведомлениях публикации, ACK и NACK только JSON object с message_id, независимо от размера задачи. Аргументы, options, actor names и failure diagnostics MUST оставаться в защищённом SQL storage и не попадать в notification payload. Приём legacy full hints SHALL сохраняться согласно Authoritative queue claim.

#### Scenario: Unprivileged listener
- **WHEN** отдельная роль с CONNECT без USAGE схемы и SELECT очереди слушает известный канал при enqueue/ACK/NACK
- **THEN** её чтение таблицы запрещено, а каждое полученное уведомление содержит только message_id и не раскрывает task data

#### Scenario: Different message sizes and namespaces
- **WHEN** публикуются малые и большие сообщения в default и custom schema/prefix областях
- **THEN** уведомления всегда ID-only, consumer читает актуальную задачу из SQL, results и retry сохраняют поведение

#### Scenario: Legacy notification reception
- **WHEN** consumer получает старое полное уведомление с устаревшими аргументами
- **THEN** consumer исполняет authoritative сохранённые данные и новое ACK/NACK содержит только ID

### Requirement: Malformed notification tolerance

Consumer SHALL пропускать недействительные JSON/object/message_id hints без исключения, закрытия sessions или освобождения locks исполняемых задач. Только boolean true scan marker SHALL запускать queue scan. ID-only и legacy full hints с действительным UUID MUST сохраняться; durable claim остаётся authoritative.

#### Scenario: Restricted sender malformed hints
- **WHEN** роль без queue privileges отправляет malformed JSON, scalar/array/null, missing ID или invalid UUID на известный enqueue channel
- **THEN** consumer сохраняет sessions и processing locks и claims следующую действительную задачу

#### Scenario: Legacy and scan control
- **WHEN** consumer получает valid UUID legacy hint либо boolean true scan marker
- **THEN** выполняется обычный durable claim либо queue scan, без доверия к sender actor/args
