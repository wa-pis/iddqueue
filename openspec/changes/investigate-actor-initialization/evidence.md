# Evidence

2026-10-06, installed Dramatiq 2.2.1 / IDDQueue checkout. inspect.getsource использован для actor, Actor.__init__, send_with_options, get_broker/set_broker и Broker.declare_actor.

In-memory probe с двумя StubBroker: actor объявлен при first, затем set_broker(second), send() оставил actor.broker=first и queue first.qsize()=1; second registry пуст до explicit declare_actor. declare_actor(second) всё ещё не сменил actor.broker. PASS.

Patch get_broker вызвал sentinel RuntimeError, custom actor_class не вызван: default resolution выполняется раньше customization. PASS.

Patch ConnectionPool.open запрещал I/O: PostgresBroker() создал closed pool и close завершился без открытия. PASS. Функциональных PG tests не запускалось; это не deferred API acceptance и не доказательство отсутствия hooks при custom middleware.

Официальные источники: https://dramatiq.io/guide.html и https://dramatiq.io/reference.html (online docs labelled 2.2.0; поведение установленной 2.2.1 подтверждено исходниками/probes). Ранние ad-hoc probes исправлены после ошибочного len(Queue) и лишнего import Results из middleware; окончательные перечисленные assertions прошли.

2026-10-07: выбранный Domain контракт реализован и проверен в add-domain-actors (9 unit + 2 separate CLI/PostgreSQL acceptance, 158 full suite). Повторный same broker no-op, другой broker и declaration after bind отвергаются, новые Domain instances обеспечивают независимую регистрацию. Async/Results/delay/callback names/native pipelines/groups проверены; обычный producer/worker, без обязательной привязки FastAPI. Dockerfile и commands подготовлены, engine недоступен; фактические контейнеры/replicas не проверялись.

## Контейнерная проверка — 2026-10-07

Существующая остановленная Colima default запущена с её containerd runtime; Docker Engine socket по-прежнему отсутствует. Проверка через colima nerdctl -- (не docker CLI). Dockerfile собран без изменений из checkout 9306ae7: image manifest sha256:a80f47a413babf51a091cc09254ffd9b8b23eef5fc7a8b5f2ce3587ffaa28c66. Отдельный postgres:18 в отдельной network iddqueue-acceptance, application DB не использовалась.

Две billing replicas, каждая --use-spawn --processes 2 --threads 4 --queues billing: оба контейнера и все четыре worker processes исполняли задачи (логи ready/Consumed). 100 add(i,1) дали результаты 1..100. notifications задача оставалась queued до запуска отдельного --processes 1 --queues notifications worker, затем вернула ожидаемый результат. Default exec CMD того же image исполнил billing и notifications tasks.

Пять samples pg_stat_activity после обработки: billing-a=16, billing-b=15 соединений. Это фактическое наблюдение данного малого запуска, не максимальная нагрузка/benchmark. Верхняя граница default worker pools для этих billing replicas: 2 replicas × 2 processes × maxconn 16 = 64, producer/другие pools учитываются отдельно; consumer reserved sessions входят в pool limit.

Graceful stop --time 30: billing-a/billing-b/notifications exited 0, логи штатного Worker shutdown, после остановки workers и producer count(pg_stat_activity для их application_name)=0. Default CMD также штатно остановлен. Полная Docker Engine-specific проверка не заявляется; portable Dockerfile/application execution подтверждены на containerd.

Точные команды и producer assertions: container-acceptance.md.

Docs links/strict MkDocs, Ruff, uv lock --check, strict OpenSpec и diff check passed. Runtime/package files не изменены; полный suite не повторялся локально для documentation-only diff. Выделенные контейнеры/network удалены, ранее остановленная Colima снова остановлена.
