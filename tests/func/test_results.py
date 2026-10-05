from uuid import uuid4

import pytest
from dramatiq import Message, get_broker
from dramatiq.results import ResultFailure, ResultMissing, ResultTimeout

from tests.func.actors import failing, saver


@pytest.mark.timeout(8)
def test_block(worker):
    message = saver.send(wait=0.5, message="test_block message.")

    # There is a race condition here between the wait= and the get_result call.
    # We want to call get_result before saver returns.
    with pytest.raises(ResultMissing):
        result = message.get_result()

    result = message.get_result(block=True)
    assert "message" in result

    result = message.get_result()
    assert "message" in result


@pytest.mark.timeout(8)
def test_failing(worker):
    message = failing.send_with_options(
        kwargs={"wait": 1},
        max_retries=0,
        store_results=True,
    )

    with pytest.raises(ResultFailure):
        message.get_result(block=True)

    with pytest.raises(ResultFailure):
        message.get_result()


@pytest.mark.timeout(8)
def test_timeout(worker):
    message = saver.send(wait=0.5, message="test_timeout message.")

    with pytest.raises(ResultTimeout):
        message.get_result(block=True, timeout=100)

    result = message.get_result(block=True)
    assert "message" in result


def test_results_alone():
    broker = get_broker()
    backend = broker.backend
    assert backend is not None

    message = Message(
        queue_name="q",
        actor_name="actor",
        args=(),
        kwargs={},
        options={},
        message_id=uuid4(),
    )

    input_ = {"msg": "Test results alone"}
    backend.store_result(message, input_, ttl=1000)
    output = backend.get_result(message, block=True, timeout=1000)
    assert input_ == output
