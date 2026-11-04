"""Adaptador de OrderNotifier que escribe en el log de la aplicación."""

import logging

from orderhub.application.ports.notifier import OrderNotifier
from orderhub.domain.entities import Order

logger = logging.getLogger(__name__)


class ConsoleOrderNotifier(OrderNotifier):
    """Sustituye el print legado; más adelante se cambia por correo o una cola
    (RF-04.1).
    """

    def order_created(self, order: Order) -> None:
        """Registra en el log (JSON) el aviso de la orden creada, con sus datos."""
        logger.info(
            "Notificando al servicio de correos para la orden ID: %s",
            order.id,
            extra={
                "event": "order_created",
                "order_id": order.id,
                "order_user_id": order.user_id,
                "product_id": order.product_id,
                "quantity": order.quantity,
                "total": order.total,
            },
        )
