"""Actors shared by the web process and the separate Dramatiq worker."""

import os

import dramatiq

from iddqueue import PostgresBroker


def make_broker():
    return PostgresBroker(
        url=os.getenv("IDDQUEUE_DATABASE_URL", ""),
        schema=os.getenv("IDDQUEUE_SCHEMA", "dramatiq"),
    )


def register_actors(broker):
    @dramatiq.actor(broker=broker, store_results=True)
    def add(a: int, b: int):
        return a + b

    return add
