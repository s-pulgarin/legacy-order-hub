"""Punto de entrada del worker: consume los eventos de órdenes de Redis (RF-04.1).

Se ejecuta como un proceso aparte de la API: `python worker.py` (en
docker-compose es el servicio `worker`). Termina limpio con SIGTERM o Ctrl+C.
"""

import signal
import threading

import redis

import config
from orderhub.adapters.inbound.queue.order_events_worker import OrderEventsWorker
from orderhub.observability.logging_config import configure_logging


def main() -> None:
    """Lee la configuración, conecta con Redis y procesa la cola hasta detenerse."""
    settings = config.load_settings()
    configure_logging(settings.log_level, json_format=settings.log_json)
    if not settings.redis_url:
        raise config.ConfigError("El worker necesita la variable REDIS_URL")

    stop = threading.Event()
    for sig in (signal.SIGTERM, signal.SIGINT):
        signal.signal(sig, lambda *_: stop.set())

    client = redis.Redis.from_url(settings.redis_url, decode_responses=True)
    OrderEventsWorker(client).run(stop)


if __name__ == "__main__":
    main()
