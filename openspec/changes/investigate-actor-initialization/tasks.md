## 1. Established behavior

- [x] 1.1 Прочитать Dramatiq 2.2.1 actor/get_broker/set_broker/declare_actor/send и текущий IDDQueue/FastAPI initialization.
- [x] 1.2 Проверить in-memory: late set_broker не перепривязывает; declare_actor не меняет actor.broker; actor_class не предотвращает default lookup; default PostgresBroker оставляет pool closed.

## 2. Investigation before API choice

- [ ] 2.1 Составить воспроизводимую import/startup матрицу: actor до/после configure, producer и spawned worker, FastAPI startup/shutdown, повторные app instances/test teardown.
- [ ] 2.2 Проверить native registration/factory и минимальный deferred adapter; оценить стабильные import handles без собственного повторения Actor API.
- [ ] 2.3 Проверить actor options/middleware validation, Results/async actors, send_with_options/timedelta, message/pipelines/groups/callbacks и pool ownership для каждого жизнеспособного варианта.
- [ ] 2.4 Описать повторную настройку, конфликт brokers, lifecycle isolation и понятную ошибку до binding; выбрать минимальный вариант и согласовать контракт.

## 3. Implementation handoff

- [ ] 3.1 Подготовить отдельный implementation change с delta specs/tests/migration/docs/FastAPI scope для выбранного API; не реализовывать runtime в исследовательском change.
