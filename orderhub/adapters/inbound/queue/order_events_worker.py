"""Adaptador de entrada que consume los eventos de órdenes desde Redis (RF-04.1).

Es "de entrada" porque, como Flask, recibe estímulos de fuera (mensajes en la
cola) y dispara trabajo. Corre en un proceso aparte (`worker.py`), así la API
nunca espera a que termine.
"""

import json
import logging
import threading
from typing import Callable, Optional

from redis.exceptions import RedisError

from orderhub.adapters.outbound.notifications.redis_notifier import (
    ORDER_EVENTS_QUEUE,
)

logger = logging.getLogger(__name__)

FAILED_SUFFIX = ":failed"
RECONNECT_DELAY_SECONDS = 1


def send_confirmation_email(event: dict) -> None:
    """Simula el envío del correo de confirmación de la orden.

    En producción aquí iría el cliente del proveedor de correo (SMTP, SendGrid,
    Azure Communication Services...). El log deja constancia del envío.
    """
    logger.info(
        "Correo de confirmación enviado (simulado) para la orden %s",
        event.get("order_id"),
        extra={
            "event": "order_confirmation_sent",
            "order_id": event.get("order_id"),
            "order_user_id": event.get("user_id"),
            "total": event.get("total"),
        },
    )


class OrderEventsWorker:
    """Saca eventos de la cola con `BRPOP` y los entrega al `handler`.

    - Un mensaje que no es JSON válido se descarta y se registra.
    - Si el `handler` falla, el mensaje va a la cola `<cola>:failed` (dead
      letter) para revisarlo después, y el worker sigue con los demás.
    - Si se corta la conexión con Redis, `run` espera y reintenta.
    """

    def __init__(
        self,
        redis_client,
        handler: Callable[[dict], None] = send_confirmation_email,
        queue: str = ORDER_EVENTS_QUEUE,
        poll_timeout: int = 5,
    ):
        """Recibe el cliente de Redis, la función que procesa cada evento y la cola."""
        self._redis = redis_client
        self._handler = handler
        self._queue = queue
        self._failed_queue = queue + FAILED_SUFFIX
        self._poll_timeout = poll_timeout

    def process_next(self) -> bool:
        """Procesa un mensaje si llega antes del timeout; devuelve True si hubo uno."""
        item = self._redis.brpop([self._queue], timeout=self._poll_timeout)
        if item is None:
            return False
        _, raw = item
        try:
            event = json.loads(raw)
        except (TypeError, ValueError):
            logger.error("Mensaje inválido descartado de la cola", extra={"raw": raw})
            return True
        try:
            self._handler(event)
        except Exception:
            logger.exception(
                "Falló el procesamiento del evento; se mueve a la cola de fallidos",
                extra={"order_id": event.get("order_id"), "queue": self._failed_queue},
            )
            self._redis.lpush(self._failed_queue, raw)
        return True

    def run(self, stop: Optional[threading.Event] = None) -> None:
        """Procesa mensajes hasta que se active `stop` (p. ej. al recibir SIGTERM)."""
        stop = stop or threading.Event()
        logger.info(
            "Worker de eventos de órdenes iniciado", extra={"queue": self._queue}
        )
        while not stop.is_set():
            try:
                self.process_next()
            except RedisError:
                # Redis caído o conexión cortada: se registra y se reintenta, en
                # lugar de tumbar el proceso. Los mensajes siguen en la cola.
                logger.warning(
                    "Error de conexión con Redis; reintentando en %s s",
                    RECONNECT_DELAY_SECONDS,
                    exc_info=True,
                )
                stop.wait(RECONNECT_DELAY_SECONDS)
        logger.info("Worker de eventos de órdenes detenido")
