import re
import subprocess

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
