import re
import subprocess
from uuid import uuid4

import psycopg
from psycopg import sql

from example import writer


def cli(*args):
    return subprocess.run(
        ["dramatiq-pg", *args], capture_output=True, text=True, check=True
    )


def test_stats():
    assert "done: " in cli("stats").stdout


def test_purge():
    assert "Deleted" in cli("purge", "--maxage", "1 second").stderr


def test_recover(pgconn):
    for i in range(8):
        writer.send(message="prefill", index=i)
    with pgconn() as curs:
        curs.execute("UPDATE dramatiq.queue SET state = 'consumed';")
    out = cli("recover", "--minage", "10 microsecond")
    assert re.search(r"(?:\d{2,}|[^0]) messages", out.stderr)


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
