"""Lifecycle and event-loop safety of the runnable FastAPI example."""

import asyncio
from threading import Event
from types import SimpleNamespace
from unittest.mock import Mock

import httpx
import pytest

from examples.fastapi import app as example


@pytest.mark.timeout(10)
def test_lifespan_and_publication(monkeypatch):
    brokers = [Mock(), Mock()]
    monkeypatch.setattr(example, "make_broker", Mock(side_effect=brokers))
    entered, release = Event(), Event()

    def send(a, b):
        entered.set()
        assert release.wait(3)
        return SimpleNamespace(message_id="accepted")

    actor = SimpleNamespace(send=send)
    monkeypatch.setattr(example, "register_actors", lambda broker: actor)

    async def check():
        async with example.app.router.lifespan_context(example.app):
            async with httpx.AsyncClient(transport=httpx.ASGITransport(app=example.app), base_url="http://test") as client:
                publication = asyncio.create_task(client.post("/tasks", json={"a": 2, "b": 3}))
                try:
                    # This coroutine can run while send waits in another thread.
                    assert await asyncio.to_thread(entered.wait, 2)
                    assert not publication.done()
                finally:
                    release.set()
                response = await publication
                assert response.status_code == 202
                assert response.json() == {"message_id": "accepted"}
                actor.send = Mock(side_effect=RuntimeError("secret DSN"))
                response = await client.post("/tasks", json={"a": 2, "b": 3})
                assert response.status_code == 503
                assert "secret" not in response.text
        brokers[0].close.assert_called_once()
        assert not hasattr(example.app.state, "add")
        async with example.app.router.lifespan_context(example.app):
            assert example.app.state.add is actor
        brokers[1].close.assert_called_once()

    asyncio.run(check())


@pytest.mark.timeout(10)
@pytest.mark.parametrize("failure", ["registration", "request"])
def test_lifespan_closes_on_error(monkeypatch, failure):
    broker = Mock()
    monkeypatch.setattr(example, "make_broker", lambda: broker)
    monkeypatch.setattr(example, "register_actors", Mock(side_effect=RuntimeError("registration")) if failure == "registration" else lambda broker: Mock())

    async def check():
        with pytest.raises(RuntimeError):
            async with example.app.router.lifespan_context(example.app):
                raise RuntimeError("request")
        broker.close.assert_called_once()
        assert not hasattr(example.app.state, "add")

    asyncio.run(check())
