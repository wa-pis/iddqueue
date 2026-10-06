# Контейнерная проверка

Выполнено 2026-10-07 через Colima containerd. Credentials ниже — только одноразовый выделенный PostgreSQL, не пользовательская база. Запускать из checkout.

```sh
colima start
colima nerdctl -- build -f examples/domains/Dockerfile -t iddqueue-domains:acceptance .
colima nerdctl -- network create iddqueue-acceptance
colima nerdctl -- run -d --name iddqueue-acceptance-db --network iddqueue-acceptance -e POSTGRES_PASSWORD=acceptance postgres:18
colima nerdctl -- exec iddqueue-acceptance-db pg_isready -U postgres
colima nerdctl -- run --rm --network iddqueue-acceptance iddqueue-domains:acceptance iddqueue --dsn postgresql://postgres:acceptance@iddqueue-acceptance-db/postgres init
```

Две billing replicas: выполнить дважды, NAME=iddqueue-billing-a/b, APP=billing-a/b.

```sh
colima nerdctl -- run -d --name "$NAME" --network iddqueue-acceptance -e "DATABASE_URL=postgresql://postgres:acceptance@iddqueue-acceptance-db/postgres?application_name=$APP" iddqueue-domains:acceptance dramatiq examples.domains.worker --use-spawn --processes 2 --threads 4 --queues billing
```

Producer запуск: сохранить Python ниже в producer.py; в отдельном терминале выполнить:

```sh
colima nerdctl -- run --rm -i --network iddqueue-acceptance -e 'DATABASE_URL=postgresql://postgres:acceptance@iddqueue-acceptance-db/postgres?application_name=producer' iddqueue-domains:acceptance python - < producer.py
```

```python
import json
import time
import psycopg
from examples.domains.billing import add
from examples.domains.notifications import notify
from examples.domains.worker import broker
try:
    pending = notify.send('domain isolation')
    messages = [add.send(i, 1) for i in range(100)]
    results = [m.get_result(backend=broker.backend, block=True, timeout=30000) for m in messages]
    assert results == list(range(1, 101))
    with psycopg.connect('postgresql://postgres:acceptance@iddqueue-acceptance-db/postgres') as conn:
        state = conn.execute('SELECT state FROM dramatiq.queue WHERE message_id=%s', (pending.message_id,)).fetchone()
        assert state == ('queued',), state
        samples=[]
        for _ in range(5):
            samples.append(conn.execute("SELECT application_name, count(*) FROM pg_stat_activity WHERE application_name IN ('billing-a','billing-b') GROUP BY application_name ORDER BY application_name").fetchall())
            time.sleep(.2)
        print('BILLING_COMPLETE_NOTIFICATIONS_QUEUED', json.dumps(samples), flush=True)
    assert pending.get_result(backend=broker.backend, block=True, timeout=60000) == 'domain isolation'
    print('ALL_DOMAINS_COMPLETE', flush=True)
finally:
    broker.close()
```

После BILLING_COMPLETE_NOTIFICATIONS_QUEUED запустить:

```sh
colima nerdctl -- run -d --name iddqueue-notifications --network iddqueue-acceptance -e 'DATABASE_URL=postgresql://postgres:acceptance@iddqueue-acceptance-db/postgres?application_name=notifications' iddqueue-domains:acceptance dramatiq examples.domains.worker --use-spawn --processes 1 --threads 4 --queues notifications
```

После ALL_DOMAINS_COMPLETE:

```sh
colima nerdctl -- stop --time 30 iddqueue-billing-a iddqueue-billing-b iddqueue-notifications
colima nerdctl -- inspect --format '{{.Name}} exit={{.State.ExitCode}} status={{.State.Status}}' iddqueue-billing-a iddqueue-billing-b iddqueue-notifications
colima nerdctl -- exec iddqueue-acceptance-db psql -U postgres -Atc "SELECT count(*) FROM pg_stat_activity WHERE application_name IN ('billing-a','billing-b','notifications','producer')"
```

Ожидаются exit 0 и count 0. Default CMD проверен отдельным контейнером без command override: add(2,3) -> 5 и notify('default CMD') -> тот же текст. После проверки удалить только контейнеры/network данного запуска и остановить ранее остановленную Colima.
