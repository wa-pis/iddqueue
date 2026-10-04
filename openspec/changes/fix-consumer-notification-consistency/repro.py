import json
from uuid import uuid4
import psycopg
from psycopg import sql, Notify
from dramatiq import Message, MessageProxy
from iddqueue import PostgresBroker, generate_init_sql
from iddqueue.broker import message_lock
schema='review_'+uuid4().hex[:8]
conn=psycopg.connect('',autocommit=True)
conn.execute(generate_init_sql(schema))
broker=PostgresBroker(schema=schema,results=False,middleware=[])
consumers=[]
try:
    m=Message('jobs','unused',(),{'value':'old'}, {})
    c=broker.consume('jobs',prefetch=10,timeout=10);consumers.append(c);c.get_listen_conn()
    broker.enqueue(m)
    broker.enqueue(m.copy(kwargs={'value':'new'}))
    c.notifies=[Notify(pid=0,channel='unused',payload=m.encode().decode())]
    got=next(c)
    stored=conn.execute(sql.SQL('SELECT message FROM {} WHERE message_id=%s').format(sql.Identifier(schema,'queue')),(m.message_id,)).fetchone()[0]
    print(json.dumps({'finding':'stale_payload','delivered':got.kwargs,'stored':stored['kwargs']}))
    c.ack(got)
    # A new pending message makes __next__ return before purge_locks.
    n=Message('jobs','unused',(),{}, {})
    broker.enqueue(n);c.notifies=[Notify(pid=0,channel='unused',payload=n.encode().decode())]
    next(c)
    locked=not conn.execute('SELECT pg_try_advisory_lock(%s)',(message_lock(m,schema=schema),)).fetchone()[0]
    print(json.dumps({'finding':'ack_lock_retained_with_backlog','locked':locked,'unlock_queue_size':c.unlock_q.qsize()}))
    big=Message('missing','unused',(),{'value':'x'*9000}, {})
    d=broker.consume('missing',timeout=10);consumers.append(d);d.get_listen_conn()
    broker.enqueue(big)
    conn.execute(sql.SQL('DELETE FROM {} WHERE message_id=%s').format(sql.Identifier(schema,'queue')),(big.message_id,))
    d.notifies=[Notify(pid=0,channel='unused',payload=json.dumps({'message_id':big.message_id}))]
    try:
        next(d)
    except Exception as error:
        print(json.dumps({'finding':'deleted_notification','exception':type(error).__name__,'text':str(error)}))
    e=Message('delay','unused',(),{}, {})
    f=broker.consume('delay',timeout=10);consumers.append(f);f.get_listen_conn()
    broker.enqueue(e);broker.enqueue(e,delay=60000)
    f.notifies=[Notify(pid=0,channel='unused',payload=e.encode().decode())]
    early=next(f)
    actual=conn.execute(sql.SQL('SELECT queue_name FROM {} WHERE message_id=%s').format(sql.Identifier(schema,'queue')),(e.message_id,)).fetchone()[0]
    print(json.dumps({'finding':'wrong_queue_claim','delivered_queue':early.queue_name,'stored_queue':actual,'eta_delivered':early.options.get('eta')}))
finally:
    for c in consumers:c.close()
    broker.close()
    conn.execute(sql.SQL('DROP SCHEMA {} CASCADE').format(sql.Identifier(schema)))
    conn.close()
