## ADDED Requirements

### Requirement: Async caller transaction publication

Система SHALL предоставлять отдельную awaitable публикацию на активной Psycopg 3 AsyncConnection в той же базе, что бизнес-данные и таблицы очереди. Она SHALL возвращать опубликованный либо ранее дедуплицированный Message, поддерживать delay и deduplication options синхронного пути, не выполнять commit/close или автоматические retries внешней транзакции. Синхронный API SHALL сохранять свой контракт.

#### Scenario: Visibility and commit
- **WHEN** приложение изменило бизнес-данные и выполнило await публикации в одной активной async транзакции
- **THEN** отдельное соединение не видит незавершённые изменения и не получает enqueue NOTIFY; после commit видны бизнес-данные и задача, доставляется уведомление

#### Scenario: External rollback
- **WHEN** приложение откатывает транзакцию после успешного await публикации
- **THEN** бизнес-данные, задача и принадлежащие этой публикации deduplication записи отменены, enqueue NOTIFY не доставляется

#### Scenario: Delay and duplicate
- **WHEN** передана задержка либо повторный действующий ключ дедупликации
- **THEN** задержка сохраняет delayed queue/ETA синхронного пути; duplicate возвращает исходный Message без второй задачи, второго уведомления и enqueue hooks повторной публикации

#### Scenario: Incompatible or inactive connection
- **WHEN** передано синхронное соединение, неподдерживаемый тип либо async соединение вне активной транзакции
- **THEN** вызов завершается понятной ошибкой до публикации без fallback на broker pool

### Requirement: Async errors and cancellation ownership

Async публикация SHALL передавать ошибки и отмену coroutine приложению без retry, подавления отмены, закрытия соединения или завершения внешней транзакции. Внутренняя составная публикация с дедупликацией SHALL использовать savepoint для атомарности своих SQL операций. Hooks SHALL описывать SQL публикацию, а не внешний commit, и оставаться синхронными.

#### Scenario: Database error
- **WHEN** запись сообщения завершается ошибкой PostgreSQL
- **THEN** ошибка передаётся caller; внутренняя составная публикация откатывает свой savepoint, решение о внешнем rollback остаётся у caller

#### Scenario: Cancellation during SQL
- **WHEN** caller отменяет coroutine во время SQL и выходит из внешней транзакции с отменой
- **THEN** отмена достигает caller, задача/ключ/NOTIFY не фиксируются; соединение не закрывается брокером и допускает использование после выполненного caller rollback

#### Scenario: Hook timing
- **WHEN** await публикации успешно завершился, а caller впоследствии откатил транзакцию
- **THEN** уже вызванные enqueue hooks не обещают commit и не отменяются; сообщение в очереди отсутствует
