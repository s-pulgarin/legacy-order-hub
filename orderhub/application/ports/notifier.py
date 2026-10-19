"""Puerto de salida para notificar eventos de órdenes (correo, cola, log...)."""

from abc import ABC, abstractmethod

from orderhub.domain.entities import Order


class OrderNotifier(ABC):
    @abstractmethod
    def order_created(self, order: Order) -> None:
        ...
