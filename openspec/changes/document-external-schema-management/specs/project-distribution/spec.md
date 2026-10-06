## ADDED Requirements

### Requirement: Explicit schema ownership
Broker SHALL не создавать и не мигрировать PostgreSQL schema автоматически при startup или выполнении задач. CLI init/upgrade SHALL выполнять DDL только по явному запросу. Приложение SHALL иметь возможность подготовить совместимую schema через внешний migration runner, используя generated SQL и согласованные schema/prefix, без обязательного вызова CLI init и без специального disable-migration flag.

#### Scenario: External migration runner
- **WHEN** приложение выполняет generate_init_sql(schema, prefix) в пустой namespace через собственный runner, затем запускает broker с теми же schema/prefix
- **THEN** отправка, выполнение и Results работают без вызова iddqueue init из приложения

#### Scenario: Runtime role without DDL permissions
- **WHEN** schema подготовлена миграционной ролью и runtime роли предоставлены необходимые права работы с данными без CREATE
- **THEN** broker выполняет задачи без DDL прав и не пытается менять schema

#### Scenario: Missing schema
- **WHEN** приложение обращается к отсутствующей schema через broker
- **THEN** операция завершается ошибкой PostgreSQL и broker не создаёт отсутствующие объекты автоматически

#### Scenario: SQL generation
- **WHEN** вызван generate_init_sql или generate_upgrade_sql
- **THEN** возвращён SQL без соединения с БД и без выполнения DDL; применение остаётся ответственностью caller

#### Scenario: Upgrade from RC2 to RC3
- **WHEN** существующая совместимая установка IDDQueue 0.13.0rc2 обновлена до 0.13.0rc3
- **THEN** Domain API работает поверх существующей storage schema без дополнительной миграции; требование не распространяется на произвольные будущие версии
