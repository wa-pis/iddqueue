from uuid import uuid4

import psycopg
from dramatiq import Message
from prometheus_client import CollectorRegistry, generate_latest
from psycopg import sql
from psycopg.types.json import Jsonb

from iddqueue import generate_init_sql
from iddqueue.metrics import (
    PostgresDomainCollector,
    PostgresQueueCollector,
    domain_statistics,
)
from iddqueue.utils import make_pool


def test_domain_snapshot_namespace_and_retention():
    schema = 'metrics_' + uuid4().hex[:12]
    pool = make_pool('')
    with psycopg.connect('', autocommit=True) as conn:
        try:
            conn.execute(generate_init_sql(schema, 'app_'))
            for queue, state, delay in [('billing', 'queued', False), ('billing.DQ', 'queued', True),
                                        ('billing.DQ', 'consumed', True), ('billing', 'done', False),
                                        ('billing.DQ', 'rejected', False), ('billing', 'cancelled', False),
                                        ('shipping.eu.DQ', 'queued', True), ('notifications', 'queued', False)]:
                message = Message(queue, 'test', (), {}, {'eta': 4102444800000} if delay else {})
                conn.execute(sql.SQL('INSERT INTO {} (message_id,queue_name,state,message,mtime) VALUES (%s,%s,%s,%s,now()-interval \'1 hour\')').format(sql.Identifier(schema, 'app_queue')),
                             (message.message_id, queue, state, Jsonb(message.asdict())))
            rows = domain_statistics(pool, schema=schema, prefix='app_', domains=['billing', 'empty', 'shipping.eu'])
            assert [r['domain'] for r in rows] == ['billing', 'empty', 'shipping.eu']
            billing, empty, dotted = rows
            assert billing['counts'] == dict(queued=2, consumed=1, done=1, rejected=1, cancelled=1)
            assert billing['ready'] == 1 and billing['scheduled'] == 2
            assert billing['oldest_ready_seconds'] >= 3600
            assert empty['ready'] == 0 and not any(empty['counts'].values())
            assert dotted['scheduled'] == 1
            assert {r['domain'] for r in domain_statistics(pool, schema=schema, prefix='app_')} == {'billing', 'shipping.eu', 'notifications'}
            assert domain_statistics(pool, schema=schema, prefix='app_', domains=[]) == []
            registry = CollectorRegistry()
            registry.register(PostgresDomainCollector(pool, schema=schema, prefix='app_', domains=['billing']))
            registry.register(PostgresQueueCollector(pool, schema=schema, prefix='app_', queue='billing'))
            text = generate_latest(registry).decode()
            assert 'iddqueue_domain_scheduled{domain="billing"} 2.0' in text
            assert 'iddqueue_queue_ready{queue="billing"} 1.0' in text
            conn.execute(sql.SQL("DELETE FROM {} WHERE state IN ('done','rejected')").format(sql.Identifier(schema, 'app_queue')))
            text = generate_latest(registry).decode()
            assert 'iddqueue_domain_messages{domain="billing",state="done"} 0.0' in text
        finally:
            pool.close()
            conn.execute(sql.SQL('DROP SCHEMA {} CASCADE').format(sql.Identifier(schema)))
