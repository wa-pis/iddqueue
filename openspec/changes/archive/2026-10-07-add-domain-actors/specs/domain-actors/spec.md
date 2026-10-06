## Purpose

Декларация доменных акторов с автоматической маршрутизацией по очередям и явной регистрацией брокера при запуске приложения.

## ADDED Requirements

### Requirement: Domain actor declaration
Domain SHALL назначать своим стандартным Dramatiq Actors очередь по имени домена и qualified actor_name, без default broker lookup или PostgreSQL I/O при import.

#### Scenario: Domain routing
- **WHEN** Domain billing объявляет charge
- **THEN** очередь billing и actor_name billing.charge, native Actor API сохраняется

### Requirement: Explicit startup registration
Domain SHALL принимать реальный broker при register, проверять actor options и collisions и запрещать enqueue до регистрации.

#### Scenario: Late DSN
- **WHEN** tasks импортированы до создания PostgresBroker(url=dsn), затем domain.register(broker)
- **THEN** существующие imported actors отправляют через этот broker

#### Scenario: Invalid startup
- **WHEN** options несовместимы или имена заняты
- **THEN** registration отклоняется до переноса actors

#### Scenario: Lifecycle
- **WHEN** register повторяется с тем же broker
- **THEN** повторная регистрация не выполняется; другой broker или новые declarations после startup запрещены

### Requirement: Native worker compatibility
Domain actors SHALL поддерживать штатные Dramatiq worker/composition APIs с process-local bootstrap.

#### Scenario: Separate worker
- **WHEN** domain actors зарегистрированы producer и spawned worker через общий DSN
- **THEN** PostgreSQL task исполняется, результат доступен, domains маршрутизируются по очередям
