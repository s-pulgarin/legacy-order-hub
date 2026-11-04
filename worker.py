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

    poll_timeout = 5
    # El timeout del socket debe superar la espera de BRPOP; si no, redis-py corta
    # la conexión mientras el worker espera mensajes en una cola vacía.
    client = redis.Redis.from_url(
        settings.redis_url,
        decode_responses=True,
        socket_timeout=poll_timeout + 5,
        health_check_interval=30,
    )
    OrderEventsWorker(client, poll_timeout=poll_timeout).run(stop)


if __name__ == "__main__":
    main()
