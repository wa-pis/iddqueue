"""HTTP publication followed by execution in a separate worker process."""

import asyncio
import os
import signal
import subprocess
from uuid import uuid4

import httpx
import psycopg
import pytest
from dramatiq import Message
from psycopg import sql

from examples.fastapi.app import app
from iddqueue import generate_init_sql


@pytest.mark.timeout(35)
def test_fastapi_worker(monkeypatch, tmp_path):
    schema = "fastapi_" + uuid4().hex
    monkeypatch.setenv("IDDQUEUE_SCHEMA", schema)
    with psycopg.connect("", autocommit=True) as conn:
        conn.execute(generate_init_sql(schema))
    worker = None
    try:
        async def check():
            nonlocal worker
            async with app.router.lifespan_context(app):
                actor = app.state.add
                async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
                    response = await client.post("/tasks", json={"a": 2, "b": 3})
                    assert response.status_code == 202
                    message_id = response.json()["message_id"]
                with psycopg.connect("", autocommit=True) as conn:
                    payload = conn.execute(sql.SQL("SELECT message FROM {}.queue WHERE message_id = %s").format(sql.Identifier(schema)), (message_id,)).fetchone()[0]
                message = Message(**payload)
                with (tmp_path / "worker.log").open("w+") as log:
                    worker = subprocess.Popen([
                        "dramatiq", "--use-spawn", "--processes=1", "--threads=1",
                        "examples.fastapi.worker",
                    ], stdout=log, stderr=subprocess.STDOUT, start_new_session=True, env=os.environ.copy())
                    try:
                        result = await asyncio.to_thread(message.get_result, backend=actor.broker.backend, block=True, timeout=15000)
                        assert result == 5
                    finally:
                        if worker.poll() is None:
                            worker.terminate()
                            try:
                                worker.wait(timeout=10)
                            except subprocess.TimeoutExpired:
                                os.killpg(worker.pid, signal.SIGKILL)
                                worker.wait(timeout=5)
                        log.seek(0)
                        print(log.read())
                pool = actor.broker.pool
            assert pool.closed
        asyncio.run(check())
    finally:
        with psycopg.connect("", autocommit=True) as conn:
            conn.execute(sql.SQL("DROP SCHEMA {} CASCADE").format(sql.Identifier(schema)))
