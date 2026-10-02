import os
import signal
import sys
from contextlib import closing, contextmanager
from shutil import copyfileobj
from subprocess import Popen, TimeoutExpired
from time import monotonic, sleep

import psycopg
import pytest


class Listener(object):
    class Timeout(Exception):
        pass

    def __init__(self):
        self.conn = self.cursor = None

    def __enter__(self):
        self.conn = psycopg.connect("", autocommit=True)
        self.cursor = self.conn.cursor()
        self.cursor.execute('LISTEN "dramatiq.default.ack";')
        self.notifies = []  # Useful for debugging.

    def __exit__(self, *_):
        self.cursor.close()
        self.conn.close()
        self.conn = self.cursor = None

    def wait(self, count=1, timeout=8):
        self.notifies = list(self.conn.notifies(timeout=timeout, stop_after=count))
        if len(self.notifies) < count:
            raise self.Timeout("Timeout")
        return self.notifies


@contextmanager
def pgconn_manager():
    conn = psycopg.connect("", autocommit=True)
    with closing(conn):
        with conn.transaction():
            curs = conn.cursor()
            with closing(curs):
                yield curs


def truncate(table):
    with pgconn_manager() as curs:
        curs.execute(f"TRUNCATE {table};")


@pytest.fixture(autouse=True)
def pgconn():
    return pgconn_manager


@pytest.fixture(scope="session", autouse=True)
def flush_queue():
    truncate("dramatiq.queue")
    yield None


@pytest.fixture()
def witness():
    truncate("functest.witness")
    yield None


@pytest.fixture()
def listener():
    return Listener()


class WorkerManager(object):
    def __init__(self, name="workers"):
        self.logfilename = f"my-{name}.log"

    def start(self):
        self.logfo = self.open_log("w+")
        self.proc = Popen(
            [
                "dramatiq",
                "--verbose",
                "--log-file",
                self.logfilename,
                "--processes=4",
                "--threads=2",
                "--use-spawn",
                "example",
            ],
            start_new_session=True,
        )
        self.watch_log(self.logfo, needle="Worker process is ready")

    def stop(self, *_):
        if self.proc.poll() is None:
            self.proc.terminate()
            try:
                self.proc.communicate(timeout=15)
            except TimeoutExpired:
                os.killpg(os.getpgid(self.proc.pid), signal.SIGKILL)
                self.proc.communicate()
        sys.stdout.write("\n")
        with open(self.logfilename) as fo:
            copyfileobj(fo, sys.stdout)
        self.logfo.close()

    def crash(self):
        pgid = os.getpgid(self.proc.pid)
        os.killpg(pgid, signal.SIGKILL)

    def open_log(self, mode="a+"):
        return open(self.logfilename, mode)

    def watch_log(self, fo, needle):
        deadline = monotonic() + 30
        while monotonic() < deadline:
            for line in fo:
                if needle in line:
                    return
            sleep(0.05)
        raise TimeoutError(f"Worker did not log {needle!r}")


@pytest.fixture(scope="session")
def worker():
    manager = WorkerManager()
    manager.start()
    try:
        yield manager
    finally:
        manager.stop()


@pytest.fixture(scope="session")
def restart_worker():
    manager = WorkerManager(name="workers-restart")
    manager.start()
    try:
        yield manager
    finally:
        manager.stop()
