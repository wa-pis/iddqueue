import json
from uuid import uuid4

import psycopg
import pytest
from dramatiq import Message
from psycopg import sql

from iddqueue import PostgresBroker, generate_init_sql


@pytest.mark.parametrize('custom', [False, True])
@pytest.mark.parametrize('size', [10, 9000])
@pytest.mark.parametrize('operation', ['enqueue', 'ack', 'nack'])
def test_notifications_hide_task_data(custom, size, operation):
    schema = 'privacy_' + uuid4().hex[:10] if custom else 'dramatiq'
    prefix = 'app_' if custom else ''
    role = 'listener_' + uuid4().hex[:10]
    broker = PostgresBroker(schema=schema, prefix=prefix, results=False, middleware=[])
    consumer = None
    message = Message('privacy', 'secret_actor', (), {'secret': 'x' * size}, {'private': 'diagnostic'})
    table = sql.Identifier(schema, prefix + 'queue')
    with psycopg.connect('', autocommit=True) as admin:
        if custom:
            admin.execute(generate_init_sql(schema, prefix))
        admin.execute(sql.SQL('CREATE ROLE {} NOLOGIN').format(sql.Identifier(role)))
        try:
            with psycopg.connect('', autocommit=True) as listener:
                admin.execute(sql.SQL('GRANT CONNECT ON DATABASE {} TO {}').format(
                    sql.Identifier(admin.info.dbname), sql.Identifier(role)))
                listener.execute(sql.SQL('SET ROLE {}').format(sql.Identifier(role)))
                assert not listener.execute(
                    'SELECT has_schema_privilege(current_user, %s, %s)', (schema, 'USAGE')
                ).fetchone()[0]
                assert not admin.execute(
                    'SELECT has_table_privilege(%s, %s, %s)',
                    (role, sql.Identifier(schema, prefix + 'queue').as_string(admin), 'SELECT'),
                ).fetchone()[0]
                with pytest.raises(psycopg.errors.InsufficientPrivilege):
                    listener.execute(sql.SQL('SELECT message FROM {}').format(table))
                channel = broker.queries.channel(message.queue_name, 'enqueue' if operation == 'enqueue' else 'ack')
                listener.execute(sql.SQL('LISTEN {}').format(sql.Identifier(channel)))
                broker.enqueue(message)
                if operation != 'enqueue':
                    consumer = broker.consume(message.queue_name, timeout=1000)
                    claimed = next(consumer)
                    assert claimed.kwargs == message.kwargs
                    (consumer.ack if operation == 'ack' else consumer.nack)(claimed)
                notifications = list(listener.notifies(timeout=2, stop_after=1))
                assert len(notifications) == 1
                assert json.loads(notifications[0].payload) == {'message_id': message.message_id}
        finally:
            if consumer:
                consumer.close()
            broker.close()
            if custom:
                admin.execute(sql.SQL('DROP SCHEMA {} CASCADE').format(sql.Identifier(schema)))
            else:
                admin.execute(sql.SQL('DELETE FROM {} WHERE message_id=%s').format(table), (message.message_id,))
            admin.execute(sql.SQL('DROP OWNED BY {}').format(sql.Identifier(role)))
            admin.execute(sql.SQL('DROP ROLE {}').format(sql.Identifier(role)))
