"""Separate storage exporter; install the optional monitoring extra."""

import argparse
import os
import signal
from threading import Event

from prometheus_client import CollectorRegistry, start_http_server

from iddqueue.metrics import PostgresDomainCollector
from iddqueue.utils import make_pool


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--schema', default='dramatiq')
    parser.add_argument('--prefix', default='')
    parser.add_argument('--domain', action='append', dest='domains')
    parser.add_argument('--host', default='127.0.0.1')
    parser.add_argument('--port', type=int, default=9192)
    args = parser.parse_args()
    stopped = Event()
    for signum in (signal.SIGINT, signal.SIGTERM):
        signal.signal(signum, lambda *_: stopped.set())
    pool = make_pool(os.environ.get('DATABASE_URL', ''))
    server = None
    try:
        registry = CollectorRegistry()
        registry.register(PostgresDomainCollector(pool, schema=args.schema, prefix=args.prefix, domains=args.domains))
        server, thread = start_http_server(args.port, addr=args.host, registry=registry)
        stopped.wait()
        server.shutdown()
        thread.join()
    finally:
        if server:
            server.server_close()
        pool.close()


if __name__ == '__main__':
    main()
