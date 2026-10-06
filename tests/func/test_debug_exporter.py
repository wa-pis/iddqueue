import os
import socket
import subprocess
import sys
import time
from pathlib import Path
from urllib.request import urlopen
from uuid import uuid4

import psycopg
from psycopg.conninfo import make_conninfo


def test_storage_exporter_scrape_and_shutdown():
    with socket.socket() as sock:
        sock.bind(('127.0.0.1', 0))
        port = sock.getsockname()[1]
    name = 'debug_' + uuid4().hex[:12]
    env = dict(os.environ, DATABASE_URL=make_conninfo('', application_name=name))
    script = Path(__file__).resolve().parents[2] / 'examples/monitoring/exporter.py'
    process = subprocess.Popen([sys.executable, str(script), '--port', str(port), '--domain', name], env=env,
                               stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True)
    try:
        deadline = time.monotonic() + 10
        while True:
            try:
                with urlopen(f'http://127.0.0.1:{port}/metrics', timeout=2) as response:
                    text = response.read().decode()
                assert f'iddqueue_domain_ready{{domain="{name}"}} 0.0' in text
                break
            except OSError:
                assert process.poll() is None
                if time.monotonic() >= deadline:
                    raise
                time.sleep(.05)
        process.terminate()
        _, error = process.communicate(timeout=10)
        assert process.returncode == 0, error
        with psycopg.connect('') as conn:
            assert conn.execute('SELECT count(*) FROM pg_stat_activity WHERE application_name=%s', (name,)).fetchone() == (0,)
    finally:
        if process.poll() is None:
            process.kill()
            process.communicate(timeout=5)
