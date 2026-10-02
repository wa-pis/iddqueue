# postgres-periodic-scheduling Specification

## Purpose

Отправлять периодические задачи по фиксированным интервалам из PostgreSQL без двойной публикации при нескольких scheduler-процессах.

## Requirements

### Requirement: Durable interval scheduling

Scheduler SHALL хранить расписание и next_run в PostgreSQL, атомарно продвигать его вместе с отправкой и не публиковать один occurrence дважды. Первая версия SHALL поддерживать UTC fixed intervals с coalesce пропущенных запусков.

#### Scenario: Competing schedulers
- **WHEN** два scheduler процесса одновременно видят одно due расписание
- **THEN** создаётся одна задача для occurrence и next_run продвигается один раз

#### Scenario: Scheduler crash
- **WHEN** scheduler падает до commit
- **THEN** следующий процесс выполняет тот же occurrence без потери

#### Scenario: Missed intervals
- **WHEN** scheduler возобновляется после нескольких пропущенных интервалов
- **THEN** создаётся одна задача, next_run переносится на ближайшее будущее значение

#### Scenario: Disabled schedule
- **WHEN** расписание отключено
- **THEN** новые occurrences не отправляются; уже queued задачи сохраняются

#### Scenario: Crash after commit
- **WHEN** scheduler погиб после commit отправки и продвижения next_run
- **THEN** задача остаётся queued; следующий tick не повторяет committed occurrence

#### Scenario: Paused destination
- **WHEN** due расписание адресует приостановленную очередь
- **THEN** occurrence публикуется queued, actor начинает выполнение после resume

#### Scenario: Schedule namespace isolation
- **WHEN** одинаковые имена расписаний используются в разных schema/prefix
- **THEN** публикация и disable в одной области не изменяют другую

#### Scenario: Foreground shutdown
- **WHEN** foreground scheduler получает SIGTERM либо SIGINT
- **THEN** текущая tick транзакция завершается, loop останавливается и CLI pool закрывается
