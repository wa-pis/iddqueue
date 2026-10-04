"""Run with uvicorn examples.fastapi.app:app from the repository root."""

import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel

from examples.fastapi.tasks import make_broker, register_actors


@asynccontextmanager
async def lifespan(app):
    broker = await asyncio.to_thread(make_broker)
    try:
        app.state.add = register_actors(broker)
        yield
    finally:
        await asyncio.to_thread(broker.close)
        if hasattr(app.state, "add"):
            del app.state.add


app = FastAPI(lifespan=lifespan)


class Addition(BaseModel):
    a: int
    b: int


@app.post("/tasks", status_code=202)
async def enqueue(body: Addition, request: Request):
    try:
        message = await asyncio.to_thread(request.app.state.add.send, body.a, body.b)
    except Exception:
        logging.getLogger(__name__).exception("Task publication failed")
        # Do not expose SQL or connection details in the HTTP response.
        raise HTTPException(status_code=503, detail="Task publication failed") from None
    return {"message_id": message.message_id}
