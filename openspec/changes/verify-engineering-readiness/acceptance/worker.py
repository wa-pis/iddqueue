import os,dramatiq
from iddqueue import PostgresBroker
from dramatiq.middleware.prometheus import Prometheus
from tasks import billing,shipping
broker=PostgresBroker(url=os.environ['DATABASE_URL'],schema='readiness_probe')
broker.add_middleware(Prometheus())
dramatiq.set_broker(broker)
billing.register(broker);shipping.register(broker)
