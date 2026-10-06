## Decisions

Переиспользовать generate_init_sql(schema, prefix) для пустой namespace и generate_upgrade_sql(schema, prefix) для поддерживаемой существующей schema. Внешний runner выполняет возвращённый SQL своей connection/transaction; broker использует тот же schema/prefix. Не вводить интеграцию с конкретным ORM/framework или флаг автоматической миграции.

## Migration Plan

В deployment выбирается один способ применения DDL: CLI init/upgrade либо внешние migration scripts. Таблицы/типы/индексы и необходимые auxiliary objects должны соответствовать контракту пакета; произвольная похожая таблица не поддерживается. init предназначен для пустой namespace; генерация SQL сама не обращается к БД. Отдельная runtime роль может работать без DDL прав. При отсутствующей schema runtime сообщает ошибку PostgreSQL, не выполняет implicit repair.

Для RC2 -> RC3 DDL не требуется; это не обещание отсутствия миграций в будущих версиях. Domain additive и не меняет storage schema.

## Verification

На dedicated PostgreSQL создать отдельную namespace внешним выполнением generated SQL, проверить broker/Results и runtime роль без CREATE; проверить отсутствие автоматического создания объектов в пустой namespace. Не проверять только факт наличия option, которой нет.
