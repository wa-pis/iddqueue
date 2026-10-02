## Purpose

Определить совместимость и поставку обновлённого Python-пакета, его CLI и тестирование в самостоятельном GitHub-проекте пользователя.

## ADDED Requirements

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
