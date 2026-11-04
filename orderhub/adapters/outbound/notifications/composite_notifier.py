"""Notificador compuesto: reparte cada evento entre varios adaptadores."""

import logging
from typing import Iterable

from orderhub.application.ports.notifier import OrderNotifier
from orderhub.domain.entities import Order

logger = logging.getLogger(__name__)


class CompositeOrderNotifier(OrderNotifier):
    """Patrón Composite: OrderService ve un solo notificador y aquí se reenvía a todos.

    Si un notificador falla, se registra el error y se sigue con los demás: la
    orden ya está confirmada y un aviso fallido no debe convertirla en un error.
    """

    def __init__(self, notifiers: Iterable[OrderNotifier]):
        """Guarda los notificadores en el orden en que se llamarán."""
        self._notifiers = list(notifiers)

    def order_created(self, order: Order) -> None:
        """Llama a `order_created` en cada notificador, aislando sus fallos."""
        for notifier in self._notifiers:
            try:
                notifier.order_created(order)
            except Exception:
                logger.exception(
                    "Falló un notificador de órdenes",
                    extra={
                        "notifier": type(notifier).__name__,
                        "order_id": order.id,
                    },
                )
