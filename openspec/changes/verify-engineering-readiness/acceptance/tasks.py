import os,time
from iddqueue import Domain
import psycopg
billing=Domain('billing')
shipping=Domain('shipping.eu')
@billing.actor(store_results=True,max_retries=1,min_backoff=50,max_backoff=50)
def work(key):
    with psycopg.connect(os.environ['DATABASE_URL']) as conn:
        attempts=conn.execute('INSERT INTO readiness_probe.probe_attempts VALUES (%s,1) ON CONFLICT(key) DO UPDATE SET n=probe_attempts.n+1 RETURNING n',(key,)).fetchone()[0]
    if key%10==0 and attempts==1:
        raise RuntimeError('deterministic first-attempt failure')
    time.sleep(.01)
    return key
@shipping.actor(store_results=True)
def echo(value):
    return value
