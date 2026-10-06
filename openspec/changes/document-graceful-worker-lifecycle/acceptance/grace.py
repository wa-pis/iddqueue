import os,time,signal,subprocess,json,re
import psycopg
from iddqueue import generate_init_sql
from pathlib import Path
from iddqueue.utils import transaction
dsn=os.environ['DATABASE_URL']
with psycopg.connect(dsn) as c:
    c.execute(generate_init_sql(schema='readiness_probe'))
    c.execute('CREATE TABLE readiness_probe.probe_attempts(key integer PRIMARY KEY,n integer)')
from worker import broker
from tasks import slow
log=open('/tmp/readiness-grace-worker.log','w')
p=subprocess.Popen(['/tmp/iddqueue-readiness-venv/bin/dramatiq','worker','--use-spawn','--processes','2','--threads','2','--queues','shipping.eu'],cwd=Path(__file__).parent,env={**os.environ,'dramatiq_prom_port':'9197','dramatiq_prom_db':'/tmp/readiness-grace-prom'},stdout=log,stderr=log,start_new_session=True)
report={}
try:
    messages=[slow.send(i+10000) for i in range(8)]
    deadline=time.monotonic()+20
    while time.monotonic()<deadline:
        with psycopg.connect(dsn) as c:
            if c.execute('SELECT count(*) FROM readiness_probe.probe_attempts').fetchone()[0]>0:break
        time.sleep(.1)
    else:raise RuntimeError('worker did not start')
    initial=set(map(int,re.findall(r"\[PID (\d+)\].*Worker process is ready",Path("/tmp/readiness-grace-worker.log").read_text())))
    p.send_signal(signal.SIGHUP)
    old=set(m.get_result(backend=broker.backend,block=True,timeout=30000) for m in messages)
    deadline=time.monotonic()+20
    while time.monotonic()<deadline:
        text=Path('/tmp/readiness-grace-worker.log').read_text()
        if text.count('Worker process is ready')>=4:break
        time.sleep(.1)
    else:raise RuntimeError('reload did not start new workers')
    after=slow.send(20000);new=after.get_result(backend=broker.backend,block=True,timeout=15000)
    assert new not in initial,(new,initial)
    report.update(reload_results=8,initial_pids=sorted(initial),completion_pids=sorted(old),new_pid=new,reloaded=True)
    final=slow.send(30000)
    deadline=time.monotonic()+10
    while time.monotonic()<deadline:
        with psycopg.connect(dsn) as c:
            if c.execute('SELECT 1 FROM readiness_probe.probe_attempts WHERE key=30000').fetchone():break
        time.sleep(.05)
    else:raise RuntimeError('final task did not start')
    began=time.monotonic();p.terminate();p.wait(timeout=20)
    assert p.returncode==0,p.returncode
    assert final.get_result(backend=broker.backend,block=True,timeout=1000)
    report.update(shutdown_exit=0,shutdown_seconds=round(time.monotonic()-began,2),inflight_result_preserved=True)
finally:
    if p.poll() is None:p.terminate();p.wait(timeout=30)
    broker.close();log.close()
    with psycopg.connect(dsn) as c:
        report['connections_after_close']=c.execute("SELECT count(*) FROM pg_stat_activity WHERE application_name='readiness-grace' AND pid<>pg_backend_pid()").fetchone()[0]
        report['attempts']=c.execute('SELECT sum(n),max(n),count(*) FROM readiness_probe.probe_attempts').fetchone()
        c.execute('DROP SCHEMA readiness_probe CASCADE')
    Path('/tmp/readiness-grace-results.json').write_text(json.dumps(report,indent=2));print(json.dumps(report),flush=True)
