## Purpose

Определить совместимость и поставку обновлённого Python-пакета, его CLI и тестирование в самостоятельном GitHub-проекте пользователя.

## Requirements

### Requirement: Supported runtime and installation
Пакет SHALL требовать Python ≥3.10,<4, Dramatiq ≥2.2.1,<3 и драйвер Psycopg 3. Установка с extra binary SHALL предоставлять бинарный драйвер. Wheel и sdist SHALL содержать необходимую SQL-схему.

#### Scenario: Wheel installation
- **WHEN** собранный wheel установлен в чистый каталог с необходимыми зависимостями
- **THEN** пакет импортируется и SQL для создания схемы доступен

### Requirement: Maintenance CLI
CLI SHALL поддерживать init, stats, purge, recover и flush с выбранными схемой и префиксом таблиц.

#### Scenario: Initialize and inspect queue
- **WHEN** init выполнен на подготовленной пустой базе и затем вызван stats
- **THEN** схема создана и CLI выводит статистику состояний сообщений

#### Scenario: Maintenance operations
- **WHEN** вызваны purge, recover или flush с соответствующими параметрами
- **THEN** сообщения удаляются либо возвращаются в очередь согласно выбранной операции

### Requirement: GitHub compatibility checks
GitHub CI SHALL проверять код и тесты на Python 3.10, 3.13 и 3.14 с PostgreSQL 14 и 18.

#### Scenario: Repository update
- **WHEN** в настроенный GitHub-репозиторий отправлен commit либо открыт pull request
- **THEN** запускается матрица проверок, а результаты каждой комбинации доступны в GitHub Actions

### Requirement: Independent project identity and attribution
Проект SHALL размещаться в новом GitHub-репозитории пользователя с согласованными именем и видимостью. Метаданные и ссылки SHALL соответствовать выбранному проекту; лицензия PostgreSQL и credits исходных участников SHALL сохраняться.

#### Scenario: GitHub project setup
- **WHEN** пользователь определил владельца, имя, видимость репозитория и идентичность Python-пакета
- **THEN** создан новый репозиторий, origin указывает на него, upstream остаётся источником исходного проекта, а метаданные согласованы с выбранной идентичностью

### Requirement: IDDQueue identity
Пакет SHALL использовать distribution name iddqueue, import iddqueue и CLI iddqueue, сохраняя исходную лицензию и attribution.

#### Scenario: Renamed wheel
- **WHEN** собран и установлен wheel IDDQueue
- **THEN** import iddqueue и команда iddqueue --version работают, а SQL schema и wire namespace остаются совместимыми с текущими данными


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
