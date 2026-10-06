from uuid import uuid4

import psycopg
import pytest
from dramatiq import Message
from psycopg import sql
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session

from iddqueue import PostgresBroker, generate_init_sql
from iddqueue.sqlalchemy import enqueue_sqlalchemy


@pytest.fixture
def area():
    schema = 'sa_' + uuid4().hex[:12]
    engine = create_engine('postgresql+psycopg://')
    broker = PostgresBroker(schema=schema, results=False, middleware=[])
    with psycopg.connect('', autocommit=True) as admin:
        admin.execute(generate_init_sql(schema))
        admin.execute(sql.SQL('CREATE TABLE {} (id uuid PRIMARY KEY)').format(sql.Identifier(schema, 'business')))
        try:
            yield schema, engine, broker, admin
        finally:
            broker.close()
            engine.dispose()
            admin.execute(sql.SQL('DROP SCHEMA {} CASCADE').format(sql.Identifier(schema)))


@pytest.mark.parametrize('session', [False, True])
@pytest.mark.parametrize('commit', [False, True])
def test_sqlalchemy_atomic_publication(area, session, commit):
    schema, engine, broker, observer = area
    message = Message('billing', 'billing.add', (2, 3), {}, {})
    observer.execute(sql.SQL('LISTEN {}').format(sql.Identifier(broker.queries.channel('billing', 'enqueue'))))
    with engine.connect() as conn:
        caller = Session(bind=conn) if session else conn
        try:
            txn = caller.begin()
            caller.execute(text(f'INSERT INTO {schema}.business VALUES (:id)'), {'id': message.message_id})
            returned = enqueue_sqlalchemy(broker, message, connection=caller)
            assert returned == message
            assert observer.execute(sql.SQL('SELECT count(*) FROM {}').format(sql.Identifier(schema, 'queue'))).fetchone() == (0,)
            assert list(observer.notifies(timeout=0)) == []
            txn.commit() if commit else txn.rollback()
            assert not conn.closed
            assert conn.execute(text('SELECT 1')).scalar_one() == 1
            for table in ['business', 'queue']:
                assert observer.execute(sql.SQL('SELECT count(*) FROM {}').format(sql.Identifier(schema, table))).fetchone() == (int(commit),)
            assert len(list(observer.notifies(timeout=.1, stop_after=1))) == int(commit)
            assert broker.pool.closed  # Publication never opens the broker pool.
        finally:
            if session:
                caller.close()


def test_nested_delay_dedup_and_error_rollback(area):
    schema, engine, broker, observer = area
    with engine.connect() as conn:
        with conn.begin():
            conn.execute(text('SELECT 1'))
            nested = conn.begin_nested()
            message = Message('billing', 'billing.add', (), {}, {})
            delayed = enqueue_sqlalchemy(broker, message, connection=conn, delay=1000)
            assert delayed.queue_name == 'billing.DQ' and 'eta' in delayed.options
            nested.rollback()
            assert conn.execute(text(f'SELECT count(*) FROM {schema}.queue')).scalar_one() == 0
            first = enqueue_sqlalchemy(broker, message, connection=conn, deduplication_key='order', deduplication_ttl=60000)
            duplicate = enqueue_sqlalchemy(broker, Message('billing', 'billing.add', (), {}, {}), connection=conn,
                                           deduplication_key='order', deduplication_ttl=60000)
            assert duplicate.message_id == first.message_id
        assert observer.execute(sql.SQL('SELECT count(*) FROM {}').format(sql.Identifier(schema, 'queue'))).fetchone() == (1,)
        with conn.begin():
            conn.execute(text('SELECT 1'))
            savepoint = conn.begin_nested()
            with pytest.raises(psycopg.errors.InvalidTextRepresentation):
                enqueue_sqlalchemy(broker, first.copy(message_id="invalid-uuid"), connection=conn)
            savepoint.rollback()
            assert conn.execute(text('SELECT 1')).scalar_one() == 1


def test_inactive_logical_transaction_and_invalid_input(area):
    _, engine, broker, _ = area
    message = Message('billing', 'billing.add', (), {}, {})
    with pytest.raises(TypeError, match='synchronous'):
        enqueue_sqlalchemy(broker, message, connection=engine)
    with engine.connect() as conn:
        with pytest.raises(ValueError, match='active'):
            enqueue_sqlalchemy(broker, message, connection=conn)
        with conn.begin():
            with pytest.raises(ValueError, match='Execute SQL'):
                enqueue_sqlalchemy(broker, message, connection=conn)
        with Session(bind=conn) as session:
            with pytest.raises(ValueError, match='active'):
                enqueue_sqlalchemy(broker, message, connection=session)
            with session.begin():
                with pytest.raises(ValueError, match='Execute SQL'):
                    enqueue_sqlalchemy(broker, message, connection=session)
    with pytest.raises(ValueError, match='active'):
        enqueue_sqlalchemy(broker, message, connection=conn)
    with Session(binds={}) as session:
        with session.begin():
            with pytest.raises(ValueError, match='explicit Connection'):
                enqueue_sqlalchemy(broker, message, connection=session)
    assert broker.pool.closed


def test_session_does_not_flush_or_manage_lifecycle(area, monkeypatch):
    _, engine, broker, _ = area
    with Session(bind=engine) as session:
        with session.begin():
            session.execute(text('SELECT 1'))
            with monkeypatch.context() as guards:
                def forbidden(*args, **kwargs):
                    raise AssertionError('adapter managed caller lifecycle')
                for name in ['flush', 'commit', 'rollback', 'close']:
                    guards.setattr(session, name, forbidden)
                enqueue_sqlalchemy(broker, Message('billing', 'billing.add', (), {}, {}), connection=session)
            assert session.execute(text('SELECT 1')).scalar_one() == 1
