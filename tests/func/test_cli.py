import subprocess
from uuid import uuid4

import psycopg
from psycopg import sql


def cli(*args):
    return subprocess.run(
        ["iddqueue", *args], capture_output=True, text=True, check=True
    )


def test_stats():
    assert "done: " in cli("stats").stdout


def test_purge():
    assert "Deleted" in cli("purge", "--maxage", "1 second").stderr


def test_recover():
    schema = "recover_" + uuid4().hex[:12]
    flags = ("--schemaname", schema)
    with psycopg.connect("", autocommit=True) as conn:
        try:
            cli(*flags, "init")
            for _ in range(8):
                conn.execute(sql.SQL(
                    "INSERT INTO {} (message_id, state, mtime) "
                    "VALUES (%s, 'consumed', now()-interval '1 hour')"
                ).format(sql.Identifier(schema, "queue")), (uuid4(),))
            out = cli(*flags, "recover", "--minage", "1 minute")
            assert "Recovered 8 messages" in out.stderr
            assert conn.execute(sql.SQL(
                "SELECT count(*) FROM {} WHERE state = 'queued'"
            ).format(sql.Identifier(schema, "queue"))).fetchone() == (8,)
        finally:
            conn.execute(sql.SQL("DROP SCHEMA {} CASCADE").format(sql.Identifier(schema)))


def test_flush():
    assert "Flushed" in cli("flush").stderr


def test_custom_schema_maintenance():
    schema = 'cli"' + uuid4().hex[:12]
    prefix = 'jobs"_'
    flags = ("--schemaname", schema, "--prefix", prefix)
    table = sql.Identifier(schema, prefix + "queue")
    states = ["queued", "consumed", "done", "rejected"]
    with psycopg.connect("", autocommit=True) as connection:
        # A second storage area must survive every operation on the first.
        control_schema = schema + "control"
        try:
            cli(*flags, "init")
            cli("--schemaname", control_schema, "init")
            for state in states:
                connection.execute(sql.SQL(
                    "INSERT INTO {} (message_id, state, mtime) VALUES (%s, %s, now()-interval '2 hours')"
                ).format(table), (uuid4(), state))
            control_id = uuid4()
            connection.execute(sql.SQL(
                "INSERT INTO {} (message_id, state, mtime) VALUES (%s, 'consumed', now()-interval '2 hours')"
            ).format(sql.Identifier(control_schema, "queue")), (control_id,))
            assert cli(*flags, "stats").stdout.splitlines() == [state + ": 1" for state in states]
            assert "Recovered 1 messages" in cli(*flags, "recover", "--minage", "1 hour").stderr
            assert "queued: 2" in cli(*flags, "stats").stdout
            assert "Deleted 2 messages" in cli(*flags, "purge", "--maxage", "1 hour").stderr
            assert "Flushed 2 messages" in cli(*flags, "flush").stderr
            assert cli(*flags, "stats").stdout.splitlines() == [state + ": 0" for state in states]
            assert connection.execute(sql.SQL("SELECT state FROM {} WHERE message_id = %s").format(
                sql.Identifier(control_schema, "queue")
            ), (control_id,)).fetchone() == ("consumed",)
        finally:
            for name in (schema, control_schema):
                connection.execute(sql.SQL("DROP SCHEMA IF EXISTS {} CASCADE").format(sql.Identifier(name)))
