"""Adaptador de OrderNotifier que cuenta las órdenes creadas en Prometheus."""

from orderhub.application.ports.notifier import OrderNotifier
from orderhub.domain.entities import Order
from orderhub.observability.metrics import Metrics


class MetricsOrderNotifier(OrderNotifier):
    """Incrementa `orderhub_orders_created_total` por cada orden confirmada."""

    def __init__(self, metrics: Metrics):
        """Recibe las métricas de la aplicación por constructor."""
        self._metrics = metrics

    def order_created(self, order: Order) -> None:
        """Suma 1 al contador de órdenes creadas."""
        self._metrics.orders_created.inc()
