import pytest
from dramatiq import Message
from sqlalchemy import create_engine, text
from sqlalchemy.ext.asyncio import AsyncSession

from iddqueue.sqlalchemy import enqueue_sqlalchemy


def test_unsupported_driver_and_async():
    message = Message('billing', 'add', (), {}, {})
    engine = create_engine('sqlite://')
    try:
        with engine.begin() as conn:
            conn.execute(text('SELECT 1'))
            with pytest.raises(ValueError, match='postgresql'):
                enqueue_sqlalchemy(object(), message, connection=conn)
        with pytest.raises(TypeError, match='synchronous'):
            enqueue_sqlalchemy(object(), message, connection=AsyncSession())
    finally:
        engine.dispose()
