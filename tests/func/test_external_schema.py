from uuid import uuid4

import psycopg
import pytest
from dramatiq import Message
from psycopg import sql

from iddqueue import PostgresBroker, generate_init_sql


def test_external_schema_without_runtime_create():
    schema = 'external_' + uuid4().hex[:12]
    role = 'runtime_' + uuid4().hex[:12]
    prefix = 'app_'
    broker = None
    consumer = None
    with psycopg.connect('', autocommit=True) as admin:
        try:
            admin.execute(generate_init_sql(schema, prefix))
            admin.execute(sql.SQL('CREATE ROLE {}').format(sql.Identifier(role)))
            admin.execute(sql.SQL('GRANT USAGE ON SCHEMA {} TO {}').format(
                sql.Identifier(schema), sql.Identifier(role)))
            admin.execute(sql.SQL('GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA {} TO {}').format(
                sql.Identifier(schema), sql.Identifier(role)))
            broker = PostgresBroker(url=dict(options=f'-c role={role}'), schema=schema, prefix=prefix)
            message = broker.enqueue(Message('billing', 'billing.add', (2, 3), {}, {}))
            with broker.pool.connection() as conn:
                assert conn.execute('SELECT has_schema_privilege(current_user, %s, %s)',
                                    (schema, 'CREATE')).fetchone() == (False,)
            consumer = broker.consume('billing', timeout=1000)
            claimed = next(consumer)
            assert claimed.message_id == message.message_id
            broker.backend.store_result(claimed, sum(claimed.args), ttl=10000)
            assert broker.backend.get_result(message, block=True, timeout=2000) == 5
            consumer.ack(claimed)
        finally:
            if consumer:
                consumer.close()
            if broker:
                broker.close()
            admin.execute(sql.SQL('DROP SCHEMA IF EXISTS {} CASCADE').format(sql.Identifier(schema)))
            admin.execute(sql.SQL('DROP ROLE IF EXISTS {}').format(sql.Identifier(role)))


def test_missing_schema_is_not_created():
    schema = 'missing_' + uuid4().hex[:12]
    broker = PostgresBroker(schema=schema)
    try:
        with pytest.raises(psycopg.errors.UndefinedTable):
            broker.enqueue(Message('billing', 'billing.add', (), {}, {}))
        with psycopg.connect('') as conn:
            assert conn.execute('SELECT to_regnamespace(%s)', (schema,)).fetchone() == (None,)
    finally:
        broker.close()
