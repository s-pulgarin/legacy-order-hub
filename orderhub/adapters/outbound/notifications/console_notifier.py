import logging

from orderhub.application.ports.notifier import OrderNotifier
from orderhub.domain.entities import Order

logger = logging.getLogger(__name__)


class ConsoleOrderNotifier(OrderNotifier):
    """Sustituye el print legado; más adelante se cambia por correo o una cola
    (RF-04.1).
    """

    def order_created(self, order: Order) -> None:
        logger.info("Notificando al servicio de correos para la orden ID: %s", order.id)
