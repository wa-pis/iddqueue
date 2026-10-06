"""One bootstrap per process, loaded by the standard Dramatiq CLI."""
import os

import dramatiq

from iddqueue import PostgresBroker

from .billing import billing
from .notifications import notifications

broker = PostgresBroker(url=os.environ.get("DATABASE_URL", ""))
dramatiq.set_broker(broker)
billing.register(broker)
notifications.register(broker)
