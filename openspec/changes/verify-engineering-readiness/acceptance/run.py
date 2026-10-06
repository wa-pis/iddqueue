import os,sys,time,json,signal,subprocess
from pathlib import Path
import psycopg
from sqlalchemy import create_engine,text
from prometheus_client import CollectorRegistry,start_http_server
from iddqueue import generate_init_sql
from iddqueue.sqlalchemy import enqueue_sqlalchemy
from iddqueue.metrics import domain_statistics,PostgresDomainCollector
assert '/tmp/iddqueue-readiness-venv/' in __import__('iddqueue').__file__
dsn=os.environ['DATABASE_URL']
with psycopg.connect(dsn) as c:
    c.execute(generate_init_sql(schema='readiness_probe'))
    c.execute('CREATE TABLE readiness_probe.business(id integer PRIMARY KEY)')
    c.execute('CREATE TABLE readiness_probe.probe_attempts(key integer PRIMARY KEY,n integer)')
from worker import broker
from tasks import work,echo
engine=create_engine('postgresql+psycopg://postgres@127.0.0.1:55433/postgres')
registry=CollectorRegistry();registry.register(PostgresDomainCollector(broker.pool,schema='readiness_probe',domains=['billing','shipping.eu','empty']))
server,thread=start_http_server(9192,addr='0.0.0.0',registry=registry)
processes=[];logs=[]
def start(index):
    env={**os.environ,'dramatiq_prom_port':str(9193+index),'dramatiq_prom_host':'0.0.0.0','dramatiq_prom_db':f'/tmp/iddqueue-readiness-prom-{index}'}
    log=open(f'/tmp/readiness-worker-{index}.log','a');logs.append(log)
    p=subprocess.Popen([str(Path(sys.executable).parent/'dramatiq'),'worker','--use-spawn','--processes','2','--threads','4','--queues','billing','shipping.eu'],env=env,cwd=Path(__file__).parent,stdout=log,stderr=log,start_new_session=True)
    processes.append(p);return p
report={};stop=False
signal.signal(signal.SIGTERM,lambda *_:globals().__setitem__('stop',True))
signal.signal(signal.SIGINT,lambda *_:globals().__setitem__('stop',True))
try:
    a=start(0);b=start(1)
    with engine.begin() as c:
        c.execute(text('INSERT INTO readiness_probe.business VALUES(1)'))
        committed=enqueue_sqlalchemy(broker,echo.message('committed'),connection=c)
    try:
        with engine.begin() as c:
            c.execute(text('INSERT INTO readiness_probe.business VALUES(2)'))
            rolled=enqueue_sqlalchemy(broker,echo.message('rollback'),connection=c)
            raise RuntimeError('rollback')
    except RuntimeError:pass
    assert committed.get_result(backend=broker.backend,block=True,timeout=30000)=='committed'
    with psycopg.connect(dsn) as c:
        assert c.execute('SELECT id FROM readiness_probe.business').fetchall()==[(1,)]
        assert c.execute('SELECT count(*) FROM readiness_probe.queue WHERE message_id=%s',(rolled.message_id,)).fetchone()==(0,)
    report['installed_atomicity']='commit/result and rollback/business/task passed'
    started=time.monotonic();messages=[];samples=[];restarted=False;key=0
    while time.monotonic()-started<120:
        batch=[work.send(i) for i in range(key,key+20)];messages.extend(batch);key+=20
        samples.append(domain_statistics(broker.pool,schema='readiness_probe'))
        if not restarted and time.monotonic()-started>35:
            os.killpg(a.pid,signal.SIGKILL);a.wait();time.sleep(.3);a=start(0);restarted=True
        time.sleep(1)
    for i,m in enumerate(messages):
        assert m.get_result(backend=broker.backend,block=True,timeout=60000)==i
    assert echo.send('dotted-domain').get_result(backend=broker.backend,block=True,timeout=15000)=='dotted-domain'
    with psycopg.connect(dsn) as c:
        report['states']=c.execute('SELECT state,count(*) FROM readiness_probe.queue GROUP BY state').fetchall()
        report['attempts']=c.execute('SELECT sum(n),max(n),count(*) FROM readiness_probe.probe_attempts').fetchone()
        report['connections_running']=c.execute("SELECT count(*) FROM pg_stat_activity WHERE application_name='readiness'").fetchone()[0]
    report.update(tasks=len(messages),seconds=round(time.monotonic()-started,2),restart='SIGKILL worker process group then new two-process worker',metrics_samples=len(samples))
    Path('/tmp/readiness-installed-soak.json').write_text(json.dumps(report,indent=2));print(json.dumps(report),flush=True)
    Path('/tmp/readiness-soak-done').touch()
    while not stop:time.sleep(.2)
finally:
    for p in processes:
        if p.poll() is None:
            p.terminate()
            try:p.wait(timeout=30)
            except subprocess.TimeoutExpired:os.killpg(p.pid,signal.SIGKILL);p.wait()
    server.shutdown();thread.join();server.server_close();engine.dispose();broker.close()
    for log in logs:log.close()
    with psycopg.connect(dsn) as c:
        print('CONNECTIONS_AFTER_CLOSE',c.execute("SELECT count(*) FROM pg_stat_activity WHERE application_name='readiness' AND pid<>pg_backend_pid()").fetchone()[0],flush=True)
        c.execute('DROP SCHEMA readiness_probe CASCADE')
