"""Billing task definitions need no settings or PostgreSQL connection."""
from iddqueue import Domain

billing = Domain("billing")


@billing.actor(store_results=True)
def add(a, b):
    return a + b
