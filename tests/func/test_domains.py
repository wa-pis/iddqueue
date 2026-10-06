import dramatiq
from psycopg.conninfo import make_conninfo

from examples.domains.billing import add, billing
from examples.domains.notifications import notifications, notify
from iddqueue import PostgresBroker
from tests.func.conftest import WorkerManager


def test_domains_separate_spawned_worker():
    broker = PostgresBroker(url=make_conninfo(application_name="domain-acceptance"))
    billing.register(broker)
    notifications.register(broker)
    worker = WorkerManager(name="domains", module="examples.domains.worker")
    try:
        worker.start()
        message = add.send(2, 3)
        assert message.queue_name == "billing"
        assert message.get_result(backend=broker.backend, block=True, timeout=15000) == 5
        message = notify.send("hello")
        assert message.queue_name == "notifications"
        assert message.get_result(backend=broker.backend, block=True, timeout=15000) == "hello"
        pipeline = dramatiq.pipeline([add.message(2, 3), add.message(4)], broker=broker)
        pipeline.run()
        assert pipeline.get_result(block=True, timeout=15000) == 9
        group = dramatiq.group([add.message(1, 2), notify.message("group")], broker=broker)
        group.run()
        assert list(group.get_results(block=True, timeout=15000)) == [3, "group"]
    finally:
        if hasattr(worker, "proc"):
            worker.stop()
        broker.close()


def test_standard_cli_queue_filter():
    from iddqueue import Domain
    from iddqueue.utils import transaction

    broker = PostgresBroker(url=make_conninfo(application_name="domain-acceptance"))
    first, second = Domain("billing"), Domain("notifications")
    add = first.actor(lambda a, b: a + b, actor_name="add", store_results=True)
    notify = second.actor(lambda text: text, actor_name="notify", store_results=True)
    first.register(broker)
    second.register(broker)
    worker = WorkerManager(name="domain-filter", module="examples.domains.worker", queues=["billing"])
    try:
        worker.start()
        pending = notify.send("filtered")
        done = add.send(4, 5)
        assert done.get_result(backend=broker.backend, block=True, timeout=15000) == 9
        with transaction(broker.pool) as cursor:
            cursor.execute("SELECT state::text FROM dramatiq.queue WHERE message_id = %s", (pending.message_id,))
            assert cursor.fetchone()[0] == "queued"
    finally:
        if hasattr(worker, "proc"):
            worker.stop()
        broker.close()
