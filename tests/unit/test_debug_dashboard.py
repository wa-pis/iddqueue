import json
from pathlib import Path


def test_dashboard_scopes_and_quantiles():
    dashboard = json.loads((Path(__file__).resolve().parents[2] / 'examples/monitoring/dashboard.json').read_text())
    assert {v['name'] for v in dashboard['templating']['list']} == {'datasource', 'worker_job', 'storage_job', 'domain'}
    for panel in dashboard['panels']:
        expression = panel['targets'][0]['expr']
        assert 'job="$' in expression and '${domain}' in expression
        assert 'or vector(0)' not in expression
        if 'histogram_quantile' in expression:
            assert 'sum by (le)' in expression and '/ 1000' in expression
        if 'iddqueue_domain_' in expression:
            assert expression.startswith('max by (domain)')
