# fork-license-preservation Specification

## Purpose

Сохранить исходную PostgreSQL License и attribution при распространении
самостоятельного форка dramatiq-pg в исходниках, wheel и sdist.

## Requirements

### Requirement: Original license preservation

Проект SHALL сохранять copyright DALIBO и полный исходный текст LICENSE,
включая разрешение и отказ от гарантий, во всех распространяемых копиях.

#### Scenario: Source distribution

- **WHEN** собран sdist форка
- **THEN** архив содержит полный исходный LICENSE с copyright DALIBO

#### Scenario: Wheel distribution

- **WHEN** собран wheel форка
- **THEN** артефакт содержит полный исходный LICENSE с copyright DALIBO

### Requirement: Attribution and license metadata

Документация SHALL указывать происхождение от dalibo/dramatiq-pg;
метаданные пакета SHALL обозначать PostgreSQL License. Собственные credits
SHALL не подменять copyright исходных участников.

#### Scenario: Fork attribution

- **WHEN** пользователь читает README и метаданные пакета
- **THEN** видит исходный проект, текущую лицензию и сохранённые исходные credits

### Requirement: Accurate distribution guidance

Документация SHALL описывать разрешённые использование, изменение и
распространение при сохранении notices, отдельно от лицензий зависимостей;
SHALL не гарантировать отсутствие любых правовых претензий.

#### Scenario: Publication guidance

- **WHEN** пользователь читает условия распространения форка
- **THEN** видит разрешение коммерческого использования и публикации при
  соблюдении LICENSE, обязанность сохранить notices и отдельные условия зависимостей
