## Decisions

Переиспользовать PostgresDomainCollector и Dramatiq Prometheus middleware. Один отдельный exporter на выбранную DB/schema/prefix; worker endpoint по replica. Grafana Classic JSON с Prometheus datasource, worker/storage jobs и domain selection. Dashboard: ready backlog, oldest-ready age, scheduled, actual inprogress, retained rejected, errors/retries/rejects за выбранный период, completion attempt rate и p50/p95 duration. Error counters считают attempts, rejects terminal dead letters, SQL rejected — retained rows; NULL/missing scrape не заменять нулём. Counters reset handled increase/rate; histogram buckets aggregated before quantile, milliseconds converted to seconds.

SQL gauges одного storage не суммировать по дублированным exporter replicas. Domain selector использует escaped regex, terminal .DQ транспортные показатели учитываются. Не labels message IDs/exceptions/DSNs; storage scope через job и exporter settings. Percentiles estimates; нет observations -> no data/NaN, не zero latency. Не включать monitoring по умолчанию/не запускать сервер внутри broker; example external process only.

## Verification

Dashboard structural and query/metric contract checks, actual processing errors/retries/reject/duration samples на dedicated PG. Проверить PromQL parser при доступном promtool; import/render Grafana только если реально выполнен, иначе limitation in evidence. Source references: https://grafana.com/docs/grafana/latest/visualizations/dashboards/build-dashboards/view-dashboard-json-model/ и https://prometheus.io/docs/practices/histograms/ .
