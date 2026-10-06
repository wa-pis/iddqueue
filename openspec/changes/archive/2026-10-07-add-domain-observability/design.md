## Decisions

Расширить существующие SQL/helpers. Предлагаемый domain_statistics(pool, *, domains=None, schema='dramatiq', prefix='') возвращает JSON-compatible snapshots: domain, counts по state, ready, scheduled, oldest_ready_seconds. Точные export names закрепить в API docs реализации. Основная очередь billing и billing.DQ агрегируются как billing; имя shipping.eu сохраняется, срезать только terminal .DQ. Без фильтра — обнаружение из storage; с фильтром — нулевые snapshots для отсутствующих доменов. Имена .DQ считают транспортным суффиксом: пользовательская queue с этим суффиксом неотличима от delayed queue, это ограничение документировать.

Один SQL snapshot/transaction для всех выбранных доменов, parameterized filters. Counts/ready/scheduled суммируются; oldest_ready_seconds — max, возраст считается от ready_at (не от времени создания). Prefetched future tasks остаются scheduled; не считать их выполняющимися лишь по consumed state. consumed означает захвачено/prefetched, не точное число executing actors.

Optional PostgresDomainCollector с labels domain/state, отдельными именами iddqueue_domain_*; регистрации без I/O, caller владеет pool. Не изменять семантику iddqueue_queue_*. TTL/purge влияет на retained done/rejected, это gauges, не rates. Обработку/ошибки/retries/duration брать из уже используемого native Dramatiq middleware и группировать по queue labels в exporter queries; проверить реальные имена/labels, ничего не обещать до acceptance. Не вводить message_id/user labels или HTTP service.

## Verification

Dedicated PG: mixed billing/billing.DQ/notifications/empty, cancelled/rejected/done, future prefetched, dotted name, schema/prefix. Scrape до/после purge и actual middleware execution. Миграция DDL не требуется.
