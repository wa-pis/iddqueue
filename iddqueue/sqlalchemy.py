"""Optional synchronous SQLAlchemy input for caller-owned transactions."""

import psycopg
from psycopg.pq import TransactionStatus
from sqlalchemy.engine import Connection
from sqlalchemy.orm import Session


def enqueue_sqlalchemy(broker, message, *, connection, delay=None,
                       deduplication_key=None, deduplication_ttl=None):
    """Publish in an already active SQLAlchemy/Psycopg 3 transaction.

    Does not flush, commit, rollback, close or retry the caller's transaction.
    Multi-bind sessions should pass the intended Connection explicitly.
    """
    if isinstance(connection, Session):
        if not connection.is_active or not connection.in_transaction():
            raise ValueError("Session requires an active transaction")
        if connection.bind is None:
            raise ValueError("Pass an explicit Connection for a multi-bind Session")
        connection = connection.connection()
    if not isinstance(connection, Connection):
        raise TypeError("Expected a synchronous SQLAlchemy Connection or Session")
    if connection.closed or connection.invalidated or not connection.in_transaction():
        raise ValueError("Connection requires an active transaction")
    dialect = connection.engine.dialect
    if dialect.name != "postgresql" or dialect.driver != "psycopg" or dialect.is_async:
        raise ValueError("Only synchronous postgresql+psycopg is supported")
    driver = connection.connection.driver_connection
    if not isinstance(driver, psycopg.Connection):
        raise TypeError("Expected a synchronous Psycopg 3 driver connection")
    if driver.info.transaction_status != TransactionStatus.INTRANS:
        raise ValueError("Execute SQL or flush explicitly to start the database transaction")
    return broker.enqueue_in_transaction(message, connection=driver, delay=delay,
                                         deduplication_key=deduplication_key,
                                         deduplication_ttl=deduplication_ttl)
