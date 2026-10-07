# Debugging queues

RC4 includes a ready-made metrics kit and domain gauges. Monitoring stays optional; no exporter or
middleware is started by the broker automatically.

## Enable processing and storage metrics

Install with `uv pip install "iddqueue[binary,monitoring]==0.13.0rc5"`.
The exporter/dashboard examples are available in the repository.
Add native processing middleware in the worker bootstrap before starting workers:

```python
from dramatiq.middleware.prometheus import Prometheus

broker.add_middleware(Prometheus())
```

Dramatiq exposes processing metrics on port 9191 by default. Configure
`dramatiq_prom_host`, `dramatiq_prom_port`, and a separate `dramatiq_prom_db`
directory per worker service. Multiple spawned processes within that service
share its multiprocess metrics directory. Do not share that directory between
independent replicas or unrelated jobs. Scrape each replica's endpoint once.

Use a fresh directory for each replica lifetime, including a restart after
SIGKILL. A hard kill skips Dramatiq's shutdown cleanup, so reusing its directory
can preserve stale `inprogress` gauges. For example, create a unique directory
before each launch and export it as `dramatiq_prom_db`. Remove an old directory
only after every process using it has exited; never clean an active replica's
files. A fresh directory resets process-local counters and loses unsampled
history. Prometheus `rate` handles counter resets, but these metrics cannot
reconstruct work lost in the crash window.

Start the separate storage exporter with the same database/schema/prefix:

```sh
# DATABASE_URL or libpq PG* settings identify the database.
uv run python examples/monitoring/exporter.py --domain billing --domain notifications
# Optional namespace:
uv run python examples/monitoring/exporter.py --schema app --prefix jobs_ --domain billing
```

This uses an existing Prometheus client HTTP server, outside the broker. Default
address is `127.0.0.1:9192`; choose `--host` and `--port` for your deployment.
SIGINT/SIGTERM stop the example and close its pool. It imports no actor modules.
An explicit domain filter keeps empty-domain gauges present. Use one exporter
per storage namespace; scraping several copies of the same snapshot must not
multiply backlog. The collector queries retained rows, so choose scrape interval
and retention appropriate to your database workload.

Example targets in your existing Prometheus configuration (replace addresses):

```yaml
scrape_configs:
  - job_name: iddqueue-workers
    static_configs:
      - targets: ['worker-a:9191', 'worker-b:9191']
  - job_name: iddqueue-storage
    static_configs:
      - targets: ['storage-exporter:9192']
```

A host/service address must be reachable from Prometheus. A localhost-bound
exporter is only reachable on its own host; choose the deployment interface when
scraping across hosts. Give unrelated databases/namespaces separate storage jobs.

## Import the dashboard

Download [dashboard.json](https://github.com/wa-pis/iddqueue/blob/main/examples/monitoring/dashboard.json)
from the checkout. In Grafana select **Dashboards → New → Import**, upload/paste
the JSON, then choose your Prometheus datasource, worker/storage job names and
domains. The file uses the Classic dashboard JSON format. No Grafana dependency
is installed in IDDQueue.

| Panel | Source | Meaning |
| --- | --- | --- |
| Ready backlog / oldest ready age | `iddqueue_domain_ready` / `iddqueue_domain_oldest_ready_seconds` | Eligible queued tasks and time waiting since eligibility |
| Scheduled tasks | `iddqueue_domain_scheduled` | Future tasks, including prefetched ones |
| Executing actors | `dramatiq_messages_inprogress` | Native processing gauge; SQL `consumed` is not this count |
| Retained rejected rows | `iddqueue_domain_messages{state="rejected"}` | Stored terminal tasks; decreases with purge |
| Errors / retries / terminal rejects in selected range | Native `*_total` counters with `increase` | Separate attempt errors, rescheduled retries, dead letters |
| Processed attempts per second | `dramatiq_messages_total` with `rate` | Completed processing attempts, including errors; not unique successful jobs |
| Duration p50 / p95 | Native duration histogram buckets | Estimated percentiles in seconds across the selected actors/replicas |
| Errors per actor per second | Native errors with `rate` | Find which qualified actor is failing |

One task may generate several errors and retries. Counter increases are estimates
for the selected interval; resets are handled by Prometheus. The dashboard
aggregates histogram buckets before computing percentiles and converts Dramatiq's
milliseconds to seconds. With no observations a percentile may be NaN/no data,
which does not mean zero latency. For SQL snapshots it uses `max`, not summing
identical exporter replicas; a single job must represent one storage namespace.
Dotted domain names are escaped in regex filters; main and `.DQ` transport queues
are selected together. The `.DQ` suffix remains reserved for delayed transport.

## Read symptoms and find the task

- Backlog age keeps rising: compare attempt throughput and execution duration;
  inspect worker availability and selected queue filters.
- Errors and retries rise: look at the actor breakdown, then logs and failed tasks.
- Terminal rejects rise: retries may be exhausted or an actor was explicitly
  rejected; inspect the exception rather than assuming every reject is a retry.
- Scheduled tasks rise without ready backlog: tasks may be waiting for ETA.
- No data: check Prometheus target `up`, scrape errors, job names, middleware and
  domain selection. Missing metrics are not a healthy zero backlog.

For the individual failed message use `iddqueue failed --help` and the optional
attempt-history APIs/CLI described in [recipes](recipes.md). IDs, arguments and
exception text belong in task inspection/logs, not metric labels. This kit adds
no automatic alert thresholds: choose thresholds from your workload's latency
and retry expectations.

References: [Grafana JSON model](https://grafana.com/docs/grafana/latest/visualizations/dashboards/build-dashboards/view-dashboard-json-model/),
[Prometheus histogram aggregation](https://prometheus.io/docs/practices/histograms/),
[domain metric semantics](domains.md#domain-monitoring).
