## Purpose

Сохранять ограниченную историю исполнения и повторов для диагностики задач, не включая аргументы actor по умолчанию.

## ADDED Requirements

### Requirement: Attempt records

Opt-in история SHALL фиксировать отдельные попытки с временем начала/окончания, исходом и ограниченным текстом ошибки. Retention SHALL быть настраиваемым; CLI SHALL читать историю страницами без payload по умолчанию.

#### Scenario: Retry history
- **WHEN** actor падает, повторяется и завершается успешно
- **THEN** история содержит отдельные failed и successful attempts с длительностью

#### Scenario: Worker crash
- **WHEN** worker погиб во время попытки
- **THEN** незавершённая попытка видна как incomplete; повтор не перезаписывает её

#### Scenario: Retention
- **WHEN** записи старше retention очищены
- **THEN** новые записи остаются, queued задачи и Results не удаляются

#### Scenario: Disabled history
- **WHEN** история не включена
- **THEN** дополнительные attempt records не записываются
