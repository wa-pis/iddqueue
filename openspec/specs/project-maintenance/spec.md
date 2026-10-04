# project-maintenance Specification

## Purpose

Обеспечить воспроизводимые проверки поставки IDDQueue, актуальную документацию
и понятные правила совместимости, участия и подготовки релизов.

## Requirements

### Requirement: Observable continuous checks

CI SHALL сохранять обязательную матрицу Python/PostgreSQL и предоставлять
ручной запуск, ограниченное время выполнения и результаты всех комбинаций
без прекращения оставшихся jobs из-за ошибки одной комбинации.

#### Scenario: Matrix failure
- **WHEN** одна комбинация завершается ошибкой
- **THEN** остальные выполняются до собственного результата, общий CI не считается успешным

#### Scenario: Manual validation
- **WHEN** maintainer запускает проверки вручную на выбранном ref
- **THEN** результаты относятся к конкретному checked-out commit

### Requirement: Installed distribution acceptance

Проверки поставки SHALL устанавливать собранный wheel вне checkout и
подтверждать import, CLI version, сохранение лицензии и доступность всех SQL
resources; обязательные и optional installations SHALL проверяться раздельно.

#### Scenario: Missing resource
- **WHEN** wheel не содержит нужный SQL resource либо установленный CLI не работает
- **THEN** acceptance завершается ошибкой даже при успешных тестах из checkout

#### Scenario: Optional monitoring
- **WHEN** установлен пакет с monitoring extra
- **THEN** monitoring доступен; base installation не обязана содержать optional monitoring dependency

### Requirement: Current user documentation

Документация SHALL описывать IDDQueue, актуальные API/CLI и SQL upgrade,
at-least-once, ограничения pause/cancellation/history/scheduler и процедуры
эксплуатации; проверки SHALL выявлять повреждённые локальные ссылки,
ошибки разметки и неработающие выбранные quickstart примеры.

#### Scenario: Documentation regression
- **WHEN** локальная ссылка сломана либо проверяемый пример не выполняется
- **THEN** docs check завершается ошибкой с указанием проблемного документа

### Requirement: Compatibility and contribution guidance

Проект SHALL документировать проверенные runtime версии, supported и
experimental public surfaces, правила breaking changes, migration guidance
и короткую процедуру contribution; issue/PR templates SHALL запрашивать
reproduction, ожидаемое поведение и фактически выполненные проверки.

#### Scenario: Compatibility change
- **WHEN** изменяется поддержка Python/PostgreSQL либо публичный контракт
- **THEN** пользователь видит изменение и необходимые действия в support policy и release notes

### Requirement: Release readiness without implicit publication

Единая команда release checks SHALL завершаться ошибкой при непрошедшем
обязательном check. Changelog SHALL отражать пользовательские изменения и
миграции; release evidence SHALL связывать результаты с commit и artifacts.
Публикация MUST оставаться отдельным явно авторизованным действием.

#### Scenario: Candidate readiness
- **WHEN** проверки выполняются для кандидата
- **THEN** evidence показывает commit, фактически выполненные проверки и непроверенные шаги; успешная проверка сама не создаёт tag и не публикует пакет

#### Scenario: Internal bookkeeping
- **WHEN** изменены только OpenSpec tasks либо внутренние CI детали
- **THEN** пользовательский changelog не заполняется внутренним журналом этих действий


### Requirement: Locked uv verification environment

Проект SHALL использовать version-controlled uv.lock для development и CI. Обязательные проверки SHALL отклонять рассогласование metadata/lock без автоматического изменения lock. Base и monitoring wheel acceptance, LICENSE/SQL resources и полная Python/PostgreSQL матрица MUST сохраняться.

#### Scenario: Stale lockfile
- **WHEN** dependency metadata изменена без обновления uv.lock
- **THEN** locked sync или lock check завершается ошибкой до успешного CI/release gate

#### Scenario: Installed wheel acceptance
- **WHEN** uv собирает wheel и sdist
- **THEN** установленный вне checkout wheel поддерживает import/CLI и все SQL resources, LICENSE сохранён в обоих форматах, base/monitoring проверены отдельно

#### Scenario: Contributor setup
- **WHEN** contributor выполняет документированные uv sync и release checks на выделенном PostgreSQL
- **THEN** установлен dev group и нужные extras; тесты, docs и сборка выполняются без Poetry
