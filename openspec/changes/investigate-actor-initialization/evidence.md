# Evidence

2026-10-06, installed Dramatiq 2.2.1 / IDDQueue checkout. inspect.getsource использован для actor, Actor.__init__, send_with_options, get_broker/set_broker и Broker.declare_actor.

In-memory probe с двумя StubBroker: actor объявлен при first, затем set_broker(second), send() оставил actor.broker=first и queue first.qsize()=1; second registry пуст до explicit declare_actor. declare_actor(second) всё ещё не сменил actor.broker. PASS.

Patch get_broker вызвал sentinel RuntimeError, custom actor_class не вызван: default resolution выполняется раньше customization. PASS.

Patch ConnectionPool.open запрещал I/O: PostgresBroker() создал closed pool и close завершился без открытия. PASS. Функциональных PG tests не запускалось; это не deferred API acceptance и не доказательство отсутствия hooks при custom middleware.

Официальные источники: https://dramatiq.io/guide.html и https://dramatiq.io/reference.html (online docs labelled 2.2.0; поведение установленной 2.2.1 подтверждено исходниками/probes). Ранние ad-hoc probes исправлены после ошибочного len(Queue) и лишнего import Results из middleware; окончательные перечисленные assertions прошли.
