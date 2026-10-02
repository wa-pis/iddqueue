import pytest
from dramatiq import Message

from iddqueue import PostgresBackend
from iddqueue.broker import message_lock
from iddqueue.utils import notification_channel


def test_channels_and_locks():
    message = Message(queue_name="same", actor_name="actor", args=(), kwargs={}, options={})
    assert notification_channel("same", "enqueue") == "dramatiq.same.enqueue"
    configurations = [("a", "bc"), ("ab", "c"), ('схема".', 'префикс".'), ("dramatiq", "x_")]
    channels = {notification_channel("очередь" * 100, "enqueue", schema=schema, prefix=prefix) for schema, prefix in configurations}
    assert len(channels) == len(configurations)
    assert all(len(channel.encode()) <= 63 for channel in channels)
    assert len(notification_channel("очередь" * 100, "enqueue").encode()) <= 63
    locks = {message_lock(message, schema=schema, prefix=prefix) for schema, prefix in configurations}
    assert len(locks) == len(configurations)
    assert all(-(2**63) <= lock < 2**63 for lock in locks)


def test_result_key_contract():
    with pytest.raises(ValueError, match="schema/prefix"):
        PostgresBackend(use_namespace_prefix_keys=True)
    backend = PostgresBackend(use_namespace_prefix_keys=False, namespace="logical")
    try:
        message = Message(queue_name="same", actor_name="actor", args=(), kwargs={}, options={})
        assert backend.build_message_key(message) == message.message_id
    finally:
        backend.close()
