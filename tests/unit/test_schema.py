def test_generate_sql():
    from iddqueue import generate_init_sql

    sql = generate_init_sql()

    assert '"dramatiq"."queue"' in sql

    sql = generate_init_sql(schema="public", prefix="dramatiq_")

    assert '"public"."dramatiq_queue"' in sql
