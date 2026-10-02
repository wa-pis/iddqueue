import time
from datetime import timedelta
from uuid import uuid4

import dramatiq
import psycopg
import pytest
from dramatiq.results import ResultFailure, ResultMissing

from example import async_value, execution_time, failing, saver, scale


@pytest.mark.timeout(15)
def test_pipeline(restart_worker):
    pipeline = dramatiq.pipeline([scale.message(3), scale.message_with_options(args=(4,))])
    pipeline.run()
    assert pipeline.get_result(block=True, timeout=8000) == 24
    assert list(pipeline.get_results(block=True, timeout=8000)) == [6, 24]

    pipeline = dramatiq.pipeline([scale.message(3, fail=True), scale.message(4)])
    pipeline.run()
    with pytest.raises(ResultFailure, match="pipeline failed"):
        pipeline.messages[0].get_result(block=True, timeout=8000)
    # A failed predecessor must not publish the next step.
    with psycopg.connect("", autocommit=True) as connection:
        assert connection.execute("SELECT count(*) FROM dramatiq.queue WHERE message_id = %s", (pipeline.messages[1].message_id,)).fetchone()[0] == 0
    with pytest.raises(ResultMissing):
        pipeline.get_result()


@pytest.mark.timeout(15)
@pytest.mark.parametrize("waits", [(0.4, 0), (0, 0.4)])
def test_group_results(restart_worker, waits):
    group = dramatiq.group([saver.message(wait=wait, value=i) for i, wait in enumerate(waits)])
    assert group.completed_count == 0
    group.run()
    fast_index = waits.index(0)
    assert group.children[fast_index].get_result(block=True, timeout=8000) == {"value": fast_index}
    assert list(group.get_results(block=True, timeout=8000)) == [{"value": 0}, {"value": 1}]
    assert group.completed_count == 2
    assert group.completed


@pytest.mark.timeout(15)
def test_async_actor(restart_worker):
    message = async_value.send({"async": True})
    assert message.get_result(block=True, timeout=8000) == {"async": True}
    message = async_value.send("value", fail=True)
    with pytest.raises(ResultFailure, match="async failed"):
        message.get_result(block=True, timeout=8000)


@pytest.mark.timeout(15)
def test_retry_exhaustion(restart_worker, witness):
    marker = str(uuid4())
    message = failing.send_with_options(
        kwargs={"message": marker}, max_retries=1, min_backoff=1, max_backoff=1,
        on_retry_exhausted="writer", store_results=True,
    )
    with pytest.raises(ResultFailure):
        message.get_result(block=True, timeout=8000)
    deadline = time.monotonic() + 5
    with psycopg.connect("", autocommit=True) as connection:
        while time.monotonic() < deadline:
            rows = connection.execute("SELECT payload FROM functest.witness WHERE payload->'args'->0->>'message_id' = %s", (message.message_id,)).fetchall()
            if rows:
                original, metadata = rows[0][0]["args"]
                assert original["actor_name"] == "failing"
                assert original["kwargs"]["message"] == marker
                assert original["options"]["retries"] == 2
                assert metadata == {"retries": 1, "max_retries": 1}
                return
            time.sleep(0.05)
    pytest.fail("Retry exhaustion callback not received")


@pytest.mark.timeout(15)
def test_timedelta_delay(restart_worker):
    started = time.time()
    message = execution_time.send_with_options(delay=timedelta(seconds=1))
    assert message.get_result(block=True, timeout=8000) >= started + 1
