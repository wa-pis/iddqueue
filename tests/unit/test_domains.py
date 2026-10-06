from datetime import timedelta
from unittest.mock import patch

import dramatiq
import pytest
from dramatiq import Actor
from dramatiq.brokers.stub import StubBroker
from dramatiq.results import Results
from dramatiq.results.backends import StubBackend

from iddqueue import Domain


def test_late_registration_keeps_imported_native_actor():
    with patch("dramatiq.actor.get_broker", side_effect=AssertionError("default lookup")):
        domain = Domain("billing")
        @domain.actor(priority=2, store_results=True)
        def add(a, b):
            return a + b
    assert isinstance(add, Actor)
    assert add(2, 3) == 5
    assert (add.actor_name, add.queue_name, add.priority) == ("billing.add", "billing", 2)
    assert add.message(2, 3).actor_name == "billing.add"
    with pytest.raises(RuntimeError, match="Register"):
        add.send(2, 3)
    broker = StubBroker()
    broker.add_middleware(Results(backend=StubBackend()))
    domain.register(broker)
    domain.register(broker)
    assert broker.get_actor("billing.add") is add
    message = add.send_with_options(args=(2, 3), delay=timedelta(seconds=1))
    assert message.queue_name == "billing.DQ"
    with pytest.raises(RuntimeError, match="another"):
        domain.register(StubBroker())
    with pytest.raises(RuntimeError, match="Declare"):
        domain.actor(lambda: None)


def test_registration_preflight_and_names():
    domain = Domain("billing")
    first = domain.actor(lambda: None, actor_name="first")
    second = domain.actor(lambda: None, actor_name="second", unknown_option=True)
    broker = StubBroker()
    with pytest.raises(ValueError, match="Undefined"):
        domain.register(broker)
    assert not broker.actors
    assert first.broker is second.broker
    other = Domain("notifications")
    actor = other.actor(lambda: None, actor_name="first")
    other.register(broker)
    assert actor.actor_name == "notifications.first"
    conflict = Domain("notifications")
    conflict.actor(lambda: None, actor_name="first")
    with pytest.raises(ValueError, match="already registered"):
        conflict.register(broker)
    with pytest.raises(TypeError):
        domain.register(None)


@pytest.mark.parametrize("name", ["", "1bad", "with space", None])
def test_invalid_domain(name):
    with pytest.raises(ValueError):
        Domain(name)


def test_domain_owns_queue_and_failed_hook_is_not_reusable():
    domain = Domain("billing")
    with pytest.raises(ValueError, match="owns"):
        domain.actor(lambda: None, queue_name="other")
    actor = domain.actor(lambda: None, actor_name="test")
    with pytest.raises(ValueError, match="already registered"):
        domain.actor(lambda: None, actor_name="test")
    broker = StubBroker()
    with patch.object(broker, "declare_actor", side_effect=RuntimeError("hook failure")):
        with pytest.raises(RuntimeError, match="hook failure"):
            domain.register(broker)
    with pytest.raises(RuntimeError, match="failed"):
        domain.register(broker)
    assert actor.broker is not broker
    with pytest.raises(RuntimeError, match="Register"):
        actor.send()


def test_native_callbacks_and_composition():
    domain = Domain("billing")
    first = domain.actor(lambda value: value, actor_name="first")
    second = domain.actor(lambda value: value, actor_name="second")
    assert first.message_with_options(on_success=second).options["on_success"] == "billing.second"
    broker = StubBroker()
    domain.register(broker)
    with patch("dramatiq.composition.get_broker", return_value=broker):
        pipeline = dramatiq.pipeline([first.message(1), second.message()])
        pipeline.run()
        group = dramatiq.group([first.message(2), second.message(3)])
        group.run()
    assert broker.queues["billing"].qsize() == 3


def test_native_async_actor_adaptation():
    import asyncio

    from dramatiq.middleware import AsyncIO

    domain = Domain("async_tasks")
    @domain.actor
    async def value(number):
        await asyncio.sleep(0)
        return number
    broker = StubBroker()
    middleware = AsyncIO()
    broker.add_middleware(middleware)
    domain.register(broker)
    middleware.before_worker_boot(broker, None)
    try:
        assert value(7) == 7
    finally:
        middleware.after_worker_shutdown(broker, None)
