"""Adaptador de OrderNotifier que publica el evento en una cola de Redis (RF-04.1).

La API solo hace un `LPUSH` (del orden de un milisegundo) y responde. El
trabajo lento, como enviar el correo de confirmación, lo hace el worker
(`worker.py`) leyendo la cola, sin bloquear la respuesta HTTP.
"""

import json
from datetime import datetime, timezone

from orderhub.application.ports.notifier import OrderNotifier
from orderhub.domain.entities import Order

ORDER_EVENTS_QUEUE = "orderhub:order_events"


def order_created_event(order: Order) -> dict:
    """Construye el evento `order_created` que viaja por la cola."""
    return {
        "event": "order_created",
        "order_id": order.id,
        "user_id": order.user_id,
        "product_id": order.product_id,
        "quantity": order.quantity,
        "total": order.total,
        "occurred_at": datetime.now(timezone.utc).isoformat(),
    }


class RedisOrderNotifier(OrderNotifier):
    """Encola cada orden confirmada como un mensaje JSON en una lista de Redis."""

    def __init__(self, redis_client, queue: str = ORDER_EVENTS_QUEUE):
        """Recibe un cliente `redis.Redis` (o compatible) y el nombre de la cola."""
        self._redis = redis_client
        self._queue = queue

    def order_created(self, order: Order) -> None:
        """Publica el evento; si Redis falla, el Composite registra el error."""
        self._redis.lpush(self._queue, json.dumps(order_created_event(order)))
