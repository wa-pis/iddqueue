## Purpose

Определить получение результатов и ошибок задач из PostgreSQL с ограниченным сроком хранения, блокирующим ожиданием и поддержкой больших значений.

## ADDED Requirements

### Requirement: Results and task failures
Backend SHALL возвращать сохранённый результат задачи и передавать сохранённую ошибку через стандартный контракт результатов Dramatiq.

#### Scenario: Stored result
- **WHEN** задача успешно завершена с сохранением результата
- **THEN** запрос результата возвращает исходное значение

#### Scenario: Stored exception
- **WHEN** задача завершилась ошибкой без дальнейших retries
- **THEN** запрос результата поднимает ResultFailure

### Requirement: TTL independent of database timezone
Backend SHALL считать истёкший результат отсутствующим. Срок хранения SHALL отсчитываться от текущего момента независимо от часового пояса сессии PostgreSQL.

#### Scenario: Expired result
- **WHEN** результат запрошен после истечения TTL без блокирующего ожидания
- **THEN** запрос поднимает ResultMissing

#### Scenario: Non-UTC timezone
- **WHEN** результат сохранён с TTL 60000 миллисекунд в сессии с часовым поясом Europe/Samara
- **THEN** он доступен сразу после сохранения и не истекает из-за смещения часового пояса

### Requirement: Blocking waits and precise timeout
Backend SHALL ожидать результат через уведомления PostgreSQL и учитывать таймаут в миллисекундах без округления до целых секунд.

#### Scenario: Subsecond timeout
- **WHEN** отсутствующий результат запрошен с block=true и timeout=100
- **THEN** ожидание завершается ResultTimeout примерно через 100 миллисекунд с допустимым накладным временем выполнения

#### Scenario: Zero timeout
- **WHEN** отсутствующий результат запрошен с block=true и timeout=0
- **THEN** запрос возвращает ResultTimeout без перехода к таймауту по умолчанию

### Requirement: Large blocking results
Backend SHALL возвращать полный результат, превышающий лимит payload NOTIFY, как при обычном чтении, так и при блокирующем ожидании.

#### Scenario: Large result arrives during wait
- **WHEN** после начала ожидания сохраняется результат из 10000 символов «ж»
- **THEN** ожидание завершается и возвращает полное значение без ошибки размера уведомления
