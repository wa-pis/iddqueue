"""Framework-independent declarations, bound explicitly before worker startup."""

import re

from dramatiq import Actor
from dramatiq.broker import Broker


class _DeclarationBroker(Broker):
    def __init__(self):
        super().__init__(middleware=[])

    def declare_queue(self, queue_name):
        # Declarations create no transport resources.
        pass

    def enqueue(self, message, *, delay=None):
        raise RuntimeError("Register the actor's Domain with a broker before sending")


class Domain:
    """One queue and qualified actor names; register once per process."""

    def __init__(self, name):
        if not isinstance(name, str) or not re.fullmatch(r"[a-zA-Z_][a-zA-Z0-9._-]*", name):
            raise ValueError("domain name must be a valid Dramatiq queue name")
        self.name = name
        self._declarations = _DeclarationBroker()
        self._broker = None
        self._failed = False

    def actor(self, fn=None, *, actor_name=None, priority=0, **options):
        def decorate(fn):
            if self._broker is not None or self._failed:
                raise RuntimeError("Declare all domain actors before registration")
            if "broker" in options or "queue_name" in options:
                raise ValueError("Domain owns the broker and queue_name")
            name = actor_name if actor_name is not None else fn.__name__
            if not isinstance(name, str) or not name:
                raise ValueError("actor_name must be a nonempty string")
            return Actor(fn, broker=self._declarations, actor_name=f"{self.name}.{name}",
                         queue_name=self.name, priority=priority, options=dict(options))
        return decorate if fn is None else decorate(fn)

    def register(self, broker):
        if self._failed:
            raise RuntimeError("Registration failed; create a new Domain and broker")
        if not isinstance(broker, Broker):
            raise TypeError("register requires a Dramatiq Broker")
        if broker is self._broker:
            return
        if self._broker is not None:
            raise RuntimeError("Domain is already registered with another broker")
        actors = list(self._declarations.actors.values())
        for actor in actors:
            invalid = set(actor.options) - broker.actor_options
            if invalid:
                raise ValueError(f"Undefined actor options for {actor.actor_name}: {sorted(invalid)}")
            if actor.actor_name in broker.actors:
                raise ValueError(f"Actor {actor.actor_name!r} is already registered")
        try:
            for actor in actors:
                actor.broker = broker
                broker.declare_actor(actor)
        except Exception:
            for actor in actors:
                actor.broker = self._declarations
            self._failed = True
            raise
        self._broker = broker
