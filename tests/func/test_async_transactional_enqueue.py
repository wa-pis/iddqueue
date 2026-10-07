import asyncio
from time import monotonic
from uuid import uuid4

import psycopg
import pytest
from dramatiq import Message
from dramatiq.common import current_millis, dq_name
from dramatiq.middleware import Middleware
from psycopg import sql
from psycopg.pq import TransactionStatus

from iddqueue import PostgresBroker, generate_init_sql


@pytest.fixture
def area():
    schema = 'async"' + uuid4().hex[:10]
    prefix = 'p"_'
    with psycopg.connect('', autocommit=True) as conn:
        conn.execute(generate_init_sql(schema, prefix))
        conn.execute(sql.SQL('CREATE TABLE {} (id uuid PRIMARY KEY)').format(
            sql.Identifier(schema, 'business')))
    broker = PostgresBroker(schema=schema, prefix=prefix, results=False, middleware=[])
    yield broker, schema, prefix
    broker.close()
    with psycopg.connect('', autocommit=True) as conn:
        conn.execute(sql.SQL('DROP SCHEMA {} CASCADE').format(sql.Identifier(schema)))


def task(queue='billing'):
    return Message(queue, 'unused', (), {'value': 'ж' * 10000}, {})


def count(conn, schema, table):
    return conn.execute(sql.SQL('SELECT count(*) FROM {}').format(
        sql.Identifier(schema, table))).fetchone()[0]


@pytest.mark.parametrize('commit', [True, False])
@pytest.mark.parametrize('batch', [True, False])
def test_visibility_and_ownership(area, commit, batch):
    broker, schema, prefix = area
    message = task()
    with psycopg.connect('', autocommit=True) as observer:
        observer.execute(sql.SQL('LISTEN {}').format(sql.Identifier(
            broker.queries.channel(message.queue_name, 'enqueue'))))

        async def run():
            async with await psycopg.AsyncConnection.connect('', autocommit=True) as conn:
                async with conn.transaction(force_rollback=not commit):
                    await conn.execute(sql.SQL('INSERT INTO {} VALUES (%s)').format(
                        sql.Identifier(schema, 'business')), (message.message_id,))
                    if batch:
                        returned = await broker.enqueue_many_in_transaction_async(
                            [message], connection=conn,
                            options=[{'deduplication_key': 'order', 'deduplication_ttl': 60000}])
                        assert returned == [message]
                    else:
                        assert await broker.enqueue_in_transaction_async(
                            message, connection=conn, deduplication_key='order',
                            deduplication_ttl=60000) == message
                    assert conn.info.transaction_status == TransactionStatus.INTRANS
                    assert count(observer, schema, prefix + 'queue') == 0
                    assert count(observer, schema, 'business') == 0
                    assert list(observer.notifies(timeout=0)) == []
                assert not conn.closed
                assert conn.info.transaction_status == TransactionStatus.IDLE
                assert (await (await conn.execute('SELECT 1')).fetchone()) == (1,)
        asyncio.run(run())
        for table in (prefix + 'queue', prefix + 'deduplication', 'business'):
            assert count(observer, schema, table) == int(commit)
        assert len(list(observer.notifies(timeout=0.1, stop_after=1))) == int(commit)


def test_options_hooks_and_nested_rollback(area):
    broker, schema, prefix = area
    events = []

    class Hooks(Middleware):
        def before_enqueue(self, broker, message, delay):
            events.append(('before', message.message_id, delay))

        def after_enqueue(self, broker, message, delay):
            events.append(('after', message.message_id, delay))

    broker.add_middleware(Hooks())
    first, second = task(), task('shipping.eu')
    started = current_millis()

    async def run():
        async with await psycopg.AsyncConnection.connect('', autocommit=True) as conn:
            async with conn.transaction():
                delayed = await broker.enqueue_in_transaction_async(
                    first, connection=conn, delay=1000,
                    deduplication_key='order', deduplication_ttl=60000)
                assert delayed.queue_name == dq_name(first.queue_name)
                assert delayed.options['eta'] >= started + 1000
                result = await broker.enqueue_many_in_transaction_async(
                    [task(), second], connection=conn,
                    options=[{'deduplication_key': 'order', 'deduplication_ttl': 60000}, {}])
                assert result == [delayed, second]
                assert len(events) == 4
                async with conn.transaction(force_rollback=True):
                    await broker.enqueue_in_transaction_async(task('nested'), connection=conn)
                # Hooks already executed; rollback doesn't retract them.
                assert len(events) == 6
            async with conn.transaction(force_rollback=True):
                returned = await broker.enqueue_many_in_transaction_async(
                    [task('plain'), task('plain2')], connection=conn,
                    options=[{}, {'delay': 1000}])
                assert [m.queue_name for m in returned] == ['plain', 'plain2.DQ']
    asyncio.run(run())
    with psycopg.connect('', autocommit=True) as conn:
        assert count(conn, schema, prefix + 'queue') == 2
        assert count(conn, schema, prefix + 'deduplication') == 1
        row = conn.execute(sql.SQL('SELECT message FROM {} WHERE message_id = %s').format(
            sql.Identifier(schema, prefix + 'queue')), (first.message_id,)).fetchone()[0]
        assert row['kwargs'] == first.kwargs


def test_invalid_inputs_and_savepoint_failure(area):
    broker, schema, prefix = area

    async def run():
        for method, value in ((broker.enqueue_in_transaction_async, task()),
                              (broker.enqueue_many_in_transaction_async, [])):
            with pytest.raises(TypeError, match='AsyncConnection'):
                await method(value, connection=object())
            with psycopg.connect('', autocommit=True) as sync:
                with pytest.raises(TypeError, match='AsyncConnection'):
                    await method(value, connection=sync)
        async with await psycopg.AsyncConnection.connect('', autocommit=True) as conn:
            with pytest.raises(ValueError, match='active transaction'):
                await broker.enqueue_in_transaction_async(task(), connection=conn)
            with pytest.raises(ValueError, match='active transaction'):
                await broker.enqueue_many_in_transaction_async([], connection=conn)
            async with conn.transaction():
                await conn.execute(sql.SQL('INSERT INTO {} VALUES (%s)').format(
                    sql.Identifier(schema, 'business')), (str(uuid4()),))
                assert await broker.enqueue_many_in_transaction_async([], connection=conn) == []
                for messages, options in (([task()] * 1001, None), ([task()], []),
                                          ([task()], [{'unknown': 1}])):
                    with pytest.raises(ValueError):
                        await broker.enqueue_many_in_transaction_async(
                            messages, connection=conn, options=options)
                for options in ([{}, {}],
                                [{'deduplication_key': 'new', 'deduplication_ttl': 60000}, {}]):
                    with pytest.raises(psycopg.errors.InvalidTextRepresentation):
                        await broker.enqueue_many_in_transaction_async(
                            [task(), task().copy(message_id='bad')], connection=conn, options=options)
                    assert conn.info.transaction_status == TransactionStatus.INTRANS
                with pytest.raises(ValueError, match='positive integer'):
                    await broker.enqueue_in_transaction_async(
                        task(), connection=conn, deduplication_key='bad', deduplication_ttl=0)
                with pytest.raises(psycopg.errors.InvalidTextRepresentation):
                    await broker.enqueue_in_transaction_async(
                        task().copy(message_id='bad'), connection=conn,
                        deduplication_key='bad', deduplication_ttl=60000)
                assert conn.info.transaction_status == TransactionStatus.INTRANS
                with pytest.raises(ValueError, match='positive integer'):
                    await broker.enqueue_many_in_transaction_async(
                        [task(), task()], connection=conn,
                        options=[{'deduplication_key': 'first', 'deduplication_ttl': 60000},
                                 {'deduplication_key': 'second', 'deduplication_ttl': 0}])
    asyncio.run(run())
    with psycopg.connect('', autocommit=True) as observer:
        assert count(observer, schema, prefix + 'queue') == 0
        assert count(observer, schema, prefix + 'deduplication') == 0
        assert count(observer, schema, 'business') == 1


@pytest.mark.parametrize('batch', [False, True])
def test_cancel_blocked_sql_without_blocking_loop(area, batch):
    broker, schema, prefix = area
    blocked = task('blocked')
    lock_id = 764384
    # A trigger blocks only the second message: the batch has already written
    # its first queue row and dedup key when cancellation occurs.
    with psycopg.connect('', autocommit=True) as observer:
        observer.execute(sql.SQL('''CREATE FUNCTION {}() RETURNS trigger LANGUAGE plpgsql AS $$
            BEGIN IF NEW.queue_name = 'blocked' THEN
                PERFORM pg_advisory_xact_lock(764384); END IF; RETURN NEW; END $$''').format(
                    sql.Identifier(schema, 'block_insert')))
        observer.execute(sql.SQL('CREATE TRIGGER block_insert BEFORE INSERT ON {} '
                                 'FOR EACH ROW EXECUTE FUNCTION {}()').format(
            sql.Identifier(schema, prefix + 'queue'), sql.Identifier(schema, 'block_insert')))
        for queue in ('billing', 'blocked'):
            observer.execute(sql.SQL('LISTEN {}').format(sql.Identifier(
                broker.queries.channel(queue, 'enqueue'))))
        observer.execute('SELECT pg_advisory_lock(%s)', (lock_id,))

        async def run():
            async with await psycopg.AsyncConnection.connect('', autocommit=True) as conn:
                async with conn.transaction():
                    await conn.execute(sql.SQL('INSERT INTO {} VALUES (%s)').format(
                        sql.Identifier(schema, 'business')), (blocked.message_id,))
                    if batch:
                        operation = broker.enqueue_many_in_transaction_async(
                            [task(), blocked], connection=conn,
                            options=[{'deduplication_key': 'first', 'deduplication_ttl': 60000}, {}])
                    else:
                        operation = broker.enqueue_in_transaction_async(blocked, connection=conn)
                    pending = asyncio.create_task(operation)
                    try:
                        async with await psycopg.AsyncConnection.connect('', autocommit=True) as monitor:
                            deadline = monotonic() + 5
                            while True:
                                row = await (await monitor.execute(
                                    'SELECT wait_event FROM pg_stat_activity WHERE pid = %s',
                                    (conn.info.backend_pid,))).fetchone()
                                if row == ('advisory',):
                                    break
                                assert monotonic() < deadline, 'publication never reached SQL lock'
                                await asyncio.sleep(0.01)
                        # Reaching here while SQL waits proves concurrent loop progress.
                        pending.cancel()
                        with pytest.raises(asyncio.CancelledError):
                            await asyncio.wait_for(pending, 5)
                        assert not conn.closed
                        if batch:
                            assert conn.info.transaction_status == TransactionStatus.INTRANS
                            assert (await (await conn.execute('SELECT 1')).fetchone()) == (1,)
                        else:
                            # Caller rolls back the failed single-statement transaction.
                            raise psycopg.Rollback()
                    finally:
                        if not pending.done():
                            pending.cancel()
                            await asyncio.gather(pending, return_exceptions=True)
                assert not conn.closed
                assert (await (await conn.execute('SELECT 1')).fetchone()) == (1,)
        try:
            asyncio.run(asyncio.wait_for(run(), 10))
            assert count(observer, schema, prefix + 'queue') == 0
            assert count(observer, schema, prefix + 'deduplication') == 0
            assert count(observer, schema, 'business') == int(batch)
            assert list(observer.notifies(timeout=0.1)) == []
        finally:
            observer.execute('SELECT pg_advisory_unlock(%s)', (lock_id,))


def test_async_connection_failure_is_not_retried(area, monkeypatch):
    broker, _, _ = area
    calls = []

    async def fail(*args):
        calls.append(1)
        raise psycopg.OperationalError('connection lost')

    monkeypatch.setattr(broker, '_enqueue_deduplicated_async', fail)

    async def run():
        async with await psycopg.AsyncConnection.connect('', autocommit=True) as conn:
            async with conn.transaction():
                with pytest.raises(psycopg.OperationalError, match='connection lost'):
                    await broker.enqueue_in_transaction_async(
                        task(), connection=conn, deduplication_key='key', deduplication_ttl=60000)
                assert len(calls) == 1
                assert not conn.closed
                assert conn.info.transaction_status == TransactionStatus.INTRANS
    asyncio.run(run())
