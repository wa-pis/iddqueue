# Evidence

2026-10-07: 4 focused tests passed; full dedicated PostgreSQL suite 175 passed in 56.17s (Python 3.13.14, PG14.20 port 55433). Native actual actor execution checks dashboard metric names/queue labels plus errors/retries/terminal rejects/histogram buckets/inprogress. Separate exporter subprocess serves selected empty domain gauges, SIGTERM exits 0 and PostgreSQL connections return to zero.

Official promtool 3.15.0 revision 5241a27fe3c6983549fccc32f6e65917408c63cd linux/arm64 checked 12 rendered dashboard expressions as recording rules: SUCCESS 12 rules. Used installed Colima containerd/nerdctl with docker.io/prom/prometheus image index sha256:efd719c99d83b060d9daefdcf00360461adf279f45ef5391f8d111892118753e. Datasource job/time/domain variables rendered using shipping.eu escaped regex. Check log /tmp/iddqueue-debug-promtool.log, input /tmp/iddqueue-debug-rules.json. Containers removed by --rm, previously stopped Colima stopped again.

Dashboard JSON structure/filter/quantile aggregation/seconds conversion/storage max checked; Grafana import/render not executed because no Grafana service was started. No live dashboard rendering claimed. PromQL syntax and referenced metrics verified, not production alert/load evaluation.

Docs link check/strict MkDocs, Ruff, uv lock --check and strict OpenSpec passed. First docs check caught an incorrectly inserted navigation entry under validation; corrected before final checks. No runtime/package version/dependency/schema change. Published RC3 untouched. Actual CI pending.

Signed implementation fd1a012f0c6408773e35a4f49c7130d9ee198ff7 verified/pushed. Actual Tests https://github.com/wa-pis/iddqueue/actions/runs/37542481082 success 6/6; Documentation https://github.com/wa-pis/iddqueue/actions/runs/37542481148 success. Main spec synced, archived 2026-10-07.
