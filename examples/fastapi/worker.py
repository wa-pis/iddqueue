"""Import inside a spawned Dramatiq worker; never reuse the web process pool."""

import dramatiq

from examples.fastapi.tasks import make_broker, register_actors

broker = make_broker()
dramatiq.set_broker(broker)
add = register_actors(broker)
