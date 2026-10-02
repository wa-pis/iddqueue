## Purpose

Отправлять периодические задачи по фиксированным интервалам из PostgreSQL без двойной публикации при нескольких scheduler-процессах.

## ADDED Requirements

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
