"""Casos de uso de órdenes de compra (RF-02, RF-03)."""

from typing import Callable, List, Optional

from orderhub.application.ports.notifier import OrderNotifier
from orderhub.application.ports.unit_of_work import UnitOfWork
from orderhub.domain.entities import Order
from orderhub.domain.exceptions import ProductNotFound


class OrderService:
    """Crea y lista órdenes de compra."""

    def __init__(self, uow_factory: Callable[[], UnitOfWork], notifier: OrderNotifier):
        """Recibe sus dependencias por constructor (Dependency Injection)."""
        self._uow_factory = uow_factory
        self._notifier = notifier

    def create_order(
        self, user_id: Optional[int], product_id: int, quantity: int
    ) -> Order:
        """Descuenta el stock y registra la orden en una sola transacción; luego
        notifica (RF-02.2, RF-03.3).

        1. Busca el producto (ProductNotFound si no existe).
        2. `product.decrease_stock(quantity)` ANTES de guardar la orden: si no
           hay stock lanza InsufficientStockException y no se guarda nada.
        3. Guarda la orden y el nuevo stock y confirma con `commit()`.

        Cualquier excepción antes del commit hace que la Unit of Work haga
        rollback, así que el stock y las órdenes quedan como estaban.
        """
        with self._uow_factory() as uow:
            product = uow.products.get(product_id)
            if product is None:
                raise ProductNotFound()

            product.decrease_stock(quantity)
            order = Order.place(user_id, product, quantity)

            uow.products.update_stock(product)
            order = uow.orders.add(order)
            uow.commit()

        self._notifier.order_created(order)
        return order

    def list_orders(self) -> List[Order]:
        """Devuelve todas las órdenes registradas."""
        with self._uow_factory() as uow:
            return uow.orders.list_all()
