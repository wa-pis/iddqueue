## Purpose

Изоляция приложений и результатов: определить проверяемый контракт этой возможности для PostgreSQL-проекта и совместимости с Dramatiq.

## ADDED Requirements

### Requirement: Application isolation

Сообщения, результаты, уведомления и блокировки SHALL быть изолированы между разными схемами/префиксами в одной базе.

#### Scenario: Same identifiers across applications

- **WHEN** два приложения используют одинаковые queue_name и message_id в разных областях хранения
- **THEN** каждое получает свои задачи и результаты; чужой lock или notification не нарушает его обработку

### Requirement: Explicit result namespace contract

Пакет SHALL документировать SQL-область результатов и SHALL не принимать параметр строкового формата ключей как незаметно работающий механизм изоляции.

#### Scenario: Structured key option

- **WHEN** пользователь включил use_namespace_prefix_keys для PostgreSQL backend с UUID-идентичностью
- **THEN** backend выдаёт понятную ошибку о неподдерживаемом формате и указывает использовать схему/префикс

### Requirement: Default compatibility

При стандартной области хранения SHALL сохраняться обычный публичный API брокера и результатов.

#### Scenario: Default configuration

- **WHEN** приложение использует настройки по умолчанию
- **THEN** сообщения и результаты доступны без явного namespace
