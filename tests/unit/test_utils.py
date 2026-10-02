import pytest

from dramatiq_pg.utils import make_pool


@pytest.mark.parametrize(
    "url, min_size, max_size",
    [
        ("", 0, 16),
        ("dbname=toto", 0, 16),
        ("postgresql:///?minconn=4", 4, 16),
        ("postgresql://host/?minconn=4&maxconn=10", 4, 10),
        ({"host": "hostname", "minconn": 10}, 10, 16),
    ],
)
def test_make_pool(url, min_size, max_size):
    pool = make_pool(url)
    assert pool.closed
    assert pool.min_size == min_size
    assert pool.max_size == max_size
    assert "minconn" not in pool.conninfo
    assert "maxconn" not in pool.conninfo
    assert pool.kwargs["autocommit"] is True
    pool.close()


def test_quote_ident():
    from dramatiq_pg.utils import quote_ident

    assert '"table"' == quote_ident("table")
    assert '"with space"' == quote_ident("with space")
    assert '"with""quote"' == quote_ident('with"quote')
