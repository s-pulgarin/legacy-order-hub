"""Métricas Prometheus de OrderHub (RNF-05.2).

Cubre las métricas RED (Rate, Errors, Duration) de la API HTTP y una métrica
de negocio. Cada instancia usa su propio `CollectorRegistry`, así se pueden
crear varias aplicaciones (por ejemplo, en las pruebas) sin conflictos.
"""

from typing import Tuple

from prometheus_client import (
    CONTENT_TYPE_LATEST,
    CollectorRegistry,
    Counter,
    Gauge,
    Histogram,
    generate_latest,
)

LATENCY_BUCKETS = (0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0)


class Metrics:
    """Agrupa los colectores Prometheus de la aplicación."""

    def __init__(self, registry: CollectorRegistry = None):
        """Crea los colectores en `registry` (uno nuevo si no se indica)."""
        self.registry = registry or CollectorRegistry()
        self.http_requests = Counter(
            "orderhub_http_requests_total",
            "Peticiones HTTP atendidas, por método, ruta y código de estado.",
            ["method", "endpoint", "status"],
            registry=self.registry,
        )
        self.http_request_duration = Histogram(
            "orderhub_http_request_duration_seconds",
            "Latencia de las peticiones HTTP en segundos, por método y ruta.",
            ["method", "endpoint"],
            buckets=LATENCY_BUCKETS,
            registry=self.registry,
        )
        self.http_requests_in_progress = Gauge(
            "orderhub_http_requests_in_progress",
            "Peticiones HTTP que se están atendiendo en este momento.",
            registry=self.registry,
        )
        self.orders_created = Counter(
            "orderhub_orders_created_total",
            "Órdenes de compra registradas con éxito.",
            registry=self.registry,
        )

    def observe_request(
        self, method: str, endpoint: str, status: int, seconds: float
    ) -> None:
        """Registra una petición terminada: suma al contador y a la latencia."""
        self.http_requests.labels(method, endpoint, str(status)).inc()
        self.http_request_duration.labels(method, endpoint).observe(seconds)

    def render(self) -> Tuple[bytes, str]:
        """Devuelve el texto de exposición de Prometheus y su content type."""
        return generate_latest(self.registry), CONTENT_TYPE_LATEST
