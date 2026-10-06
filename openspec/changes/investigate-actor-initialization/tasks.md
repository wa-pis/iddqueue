## 1. Established behavior

- [x] 1.1 Прочитать Dramatiq 2.2.1 actor/get_broker/set_broker/declare_actor/send и текущий IDDQueue/FastAPI initialization.
- [x] 1.2 Проверить in-memory: late set_broker не перепривязывает; declare_actor не меняет actor.broker; actor_class не предотвращает default lookup; default PostgresBroker оставляет pool closed.

## 2. Investigation before API choice

- [x] 2.1 Составить воспроизводимую import/startup матрицу: actor до/после startup с поздним DSN, обычный producer и spawned worker, повторные конфигурации/test teardown; FastAPI только optional integration.
- [x] 2.2 Проверить native registration/factory и минимальный deferred adapter; оценить стабильные import handles без собственного повторения Actor API.
- [x] 2.3 Проверить actor options/middleware validation, Results/async actors, send_with_options/timedelta, message/pipelines/groups/callbacks и pool ownership для каждого жизнеспособного варианта.
- [x] 2.4 Описать повторную настройку, конфликт brokers, lifecycle isolation и понятную ошибку до binding; выбрать минимальный вариант и согласовать контракт.

- [x] 2.5 Проверить доменные billing/notifications modules, стабильные imports/.send(), names/queue routing и одну app.worker точку сборки; сравнить общий broker с явными domain registries.
- [ ] 2.6 Проверить штатный CLI: all queues/queue filter, несколько процессов и реплик, process-local pools и graceful shutdown; записать точные проверенные команды и connection budget.
- [x] 2.7 Спланировать минимальный Docker application example: один image/entry point, exec CMD, поздний DSN/runtime settings, отдельные queue-filtered containers без собственного worker CLI. Контейнерные проверки отмечать выполненными только после фактического запуска.
- [x] 2.8 Зафиксировать границы domain isolation: queue routing отдельно от schema/prefix/DB-role access, duplicate actor names и независимые lifecycle настройки.

## 3. Implementation handoff

- [x] 3.1 Подготовить отдельный implementation change с delta specs/tests/migration/docs/framework-independent bootstrap и Docker example scope; FastAPI optional для выбранного API; не реализовывать runtime в исследовательском change.

Примечание: 2.7 выполнен как planning/application example, не Docker runtime acceptance. В 2.6 standard four-process spawn/queue filter проверены; multi-container replicas/connection budget measurement остаются непроверенными при недоступном Docker engine.
