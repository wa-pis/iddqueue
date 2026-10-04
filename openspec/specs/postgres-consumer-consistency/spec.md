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
