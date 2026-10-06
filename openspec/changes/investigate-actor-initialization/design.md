## Context

Исходный код установленного Dramatiq 2.2.1: actor decorator выбирает broker через broker or get_broker(), проверяет middleware actor_options, затем вызывает actor_class. Actor.__init__ сохраняет self.broker и вызывает declare_actor. send_with_options публикует через self.broker. set_broker меняет только global_broker; Broker.declare_actor не перепривязывает Actor.broker.

IDDQueue make_pool использует open=False; default PostgresBroker construction не открывает pool. Нет нужды приравнивать импорт broker к немедленному SQL I/O, но actor declaration всё равно выполняет registration/middleware hooks.

FastAPI example сейчас register_actors(broker) создаёт actor внутри factory; lifecycle явный, однако стабильного importable add нет. Требуется отделить декларацию задач от конфигурации процесса.

## Options

1. Native bootstrap: set_broker до import actors. Минимум кода, стандартный decorator/.send(), но остаётся зависимость от порядка импорта; не полностью решает поставленную проблему.
2. Явная factory/register_actors(broker): штатные Actors, подходит lifecycle и нескольким brokers, но callers должны получать handles; изучить возможность сохранить удобство импортов без глобального singleton.
3. Deferred declarations/binding: позволяет tasks import до startup и стабильный .send(); потребуется минимальный адаптер. Не утверждать iddqueue.actor/configure заранее. Проверить native extension points; actor_class сам по себе недостаточен.
4. Перепривязка существующих actors: изменение actor.broker вместе с registration не считать готовым решением. Старые registry, middleware validation/hooks, Results и повторная настройка требуют проверки; исключить незаметную смену backend после отправки.

## Decision Criteria

Импорт tasks без PostgreSQL connection и default broker resolution; producer/worker инициализируются один раз на процесс. До настройки enqueue выдаёт понятную ошибку. После настройки .send()/send_with_options отправляют в заданный PostgreSQL broker. Сохраняются actor_name/queue/options/priority, middleware validation, async adaptation, message/scheduling, pipelines/groups, Results и callbacks.

Повторная настройка same broker, conflicting broker, two app instances и tests teardown должны иметь определённый контракт. Pool ownership/close остаётся явным, multiprocessing spawn получает отдельную process initialization. Не обещать hot reconfiguration.

## Open Decisions

Один configurable broker на процесс или независимые registries для нескольких приложений; API названия/exports; прямой вызов actor до startup; допускается ли построение message/pipeline до binding; момент проверки middleware options. Предпочтение Ponytail: native hooks и standard Actors, без полного proxy повторяющего Dramatiq API, monkeypatch глобального Dramatiq и скрытого default broker.

## Next Step

Сначала воспроизводимые probes/import matrix и сравнение вариантов. Только затем согласовать выбранный контракт и отдельный implementation proposal/spec/tasks.
