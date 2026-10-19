"""Puerto de salida para notificar eventos de órdenes (correo, cola, log...)."""

from abc import ABC, abstractmethod

from orderhub.domain.entities import Order


class OrderNotifier(ABC):
    """Avisa a sistemas externos de los eventos de órdenes."""

    @abstractmethod
    def order_created(self, order: Order) -> None:
        """Notifica que `order` se registró correctamente."""
