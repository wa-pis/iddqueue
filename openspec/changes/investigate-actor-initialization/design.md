## Context

Исходный код установленного Dramatiq 2.2.1: actor decorator выбирает broker через broker or get_broker(), проверяет middleware actor_options, затем вызывает actor_class. Actor.__init__ сохраняет self.broker и вызывает declare_actor. send_with_options публикует через self.broker. set_broker меняет только global_broker; Broker.declare_actor не перепривязывает Actor.broker.

IDDQueue make_pool использует open=False; default PostgresBroker construction не открывает pool. Нет нужды приравнивать импорт broker к немедленному SQL I/O, но actor declaration всё равно выполняет registration/middleware hooks.

FastAPI example сейчас register_actors(broker) создаёт actor внутри factory; это лишь один пример lifecycle, не основа нового API. Главный сценарий: обычный Python producer и Dramatiq worker. Требуется отделить декларацию задач от конфигурации процесса.

## Options

1. Native bootstrap: set_broker до import actors. Минимум кода, стандартный decorator/.send(), но остаётся зависимость от порядка импорта; не полностью решает поставленную проблему.
2. Явная factory/register_actors(broker): штатные Actors, подходит lifecycle и нескольким brokers, но callers должны получать handles; изучить возможность сохранить удобство импортов без глобального singleton.
3. Deferred declarations/binding: позволяет tasks import до startup и стабильный .send(); потребуется минимальный адаптер. Не утверждать iddqueue.actor/configure заранее. Проверить native extension points; actor_class сам по себе недостаточен.
4. Перепривязка существующих actors: изменение actor.broker вместе с registration не считать готовым решением. Старые registry, middleware validation/hooks, Results и повторная настройка требуют проверки; исключить незаметную смену backend после отправки.

## Decision Criteria

Импорт tasks без PostgreSQL connection и default broker resolution; producer/worker инициализируются один раз на процесс. До настройки enqueue выдаёт понятную ошибку. После настройки .send()/send_with_options отправляют в заданный PostgreSQL broker. Сохраняются actor_name/queue/options/priority, middleware validation, async adaptation, message/scheduling, pipelines/groups, Results и callbacks.

Повторная настройка same broker, conflicting broker, two app instances и tests teardown должны иметь определённый контракт. Pool ownership/close остаётся явным, multiprocessing spawn получает отдельную process initialization. Не обещать hot reconfiguration.

## Agreed Application Scenarios

- DSN может поступать из settings/config loader при startup, а не только PG* environment до import. PostgresBroker(url=dsn) — существующий интерфейс; новые configure/bind/register API пока только обсуждаемые варианты.
- Домены billing/notifications содержат actors и бизнес-логику, не читают credentials и не создают собственные PostgreSQL pools при import. Callers хотят стабильный import actor и .send(), без передачи bootstrap повсюду.
- Одна app.worker точка входа загружает settings, создаёт process-local broker и явно собирает выбранные доменные actors. Порядок импорта модулей tasks до/после startup должен входить в acceptance.
- Основной минимальный вариант — один broker/DSN и отдельные queue names для доменов. Отдельные brokers/DSN — изучаемая возможность, не обязательная реализация нескольких backends в одном Dramatiq worker.
- Несколько worker processes/container replicas используют общую PostgreSQL очередь; pool создаётся отдельно в каждом процессе. Проверить spawn, отсутствие переноса открытого pool через fork, число соединений и shutdown.
- Штатный CLI Dramatiq запускает app.worker; --queues выбирает доменную очередь. Проверить фактический argparse синтаксис команд, import/load broker, registration в дочерних процессах и multi-domain task routing.
- Один Docker image приложения использует exec-form CMD с Dramatiq --use-spawn; DSN передаётся через runtime environment/settings или secret injection, не baked into image. Тот же entry point запускает все очереди либо отдельные контейнеры с queue filters.
- Docker — deploy example приложения, не новая runtime dependency IDDQueue. Собственный worker/process manager CLI, auto-discovery magic и container pipeline не требуются.
- Разделение модулей/очередей отделяет код/нагрузку, не является security isolation. Schema/prefix разделяют storage/notification/lock domains; настоящая access isolation требует DB roles/databases. Names actors/queues между доменами не должны случайно конфликтовать.
- FastAPI — optional integration check после framework-independent contract, не обязательный framework и не источник настроек API.

## Open Decisions

Для одного startup и нескольких доменов: общий registry или явные domain registries; поддержка нескольких независимых конфигураций и её ограничения; API названия/exports; прямой вызов actor до startup; допускается ли построение message/pipeline до binding; момент проверки middleware options. Предпочтение Ponytail: native hooks и standard Actors, без полного proxy повторяющего Dramatiq API, monkeypatch глобального Dramatiq и скрытого default broker.

## Next Step

Сначала воспроизводимые probes/import matrix и сравнение вариантов. Только затем согласовать выбранный контракт и отдельный implementation proposal/spec/tasks.

## Selected Contract — 2026-10-07

После уточнений пользователя выбран явный Domain(name): queue/name derivation и late register(broker), native Actors вместо proxy/monkeypatch. Реализация в add-domain-actors; один process bootstrap загружает DSN и domains, штатный CLI и Docker application example. FastAPI не требуется. Domain objects bind once; независимые конфигурации используют новые Domain instances. Docker engine недоступен, multi-container replica acceptance остаётся отдельной непроверенной частью исследования.
