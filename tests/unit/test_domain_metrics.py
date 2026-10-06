import pytest
from prometheus_client import CollectorRegistry

from iddqueue.metrics import PostgresDomainCollector, domain_statistics


def test_registration_does_not_use_pool():
    CollectorRegistry().register(PostgresDomainCollector(object(), domains=['billing']))


@pytest.mark.parametrize('domains', ['billing', [''], ['billing.DQ']])
def test_invalid_filter(domains):
    with pytest.raises((TypeError, ValueError)):
        domain_statistics(object(), domains=domains)
