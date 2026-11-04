"""Pruebas de las métricas Prometheus y de los notificadores asociados (RNF-05.2)."""

import logging

from orderhub.adapters.outbound.notifications.composite_notifier import (
    CompositeOrderNotifier,
)
from orderhub.adapters.outbound.notifications.metrics_notifier import (
    MetricsOrderNotifier,
)
from orderhub.domain.entities import Order
from orderhub.observability.metrics import Metrics
from tests.unit.fakes import FakeNotifier

ORDER = Order(1, 2, 1, 3, 3600.0)


def _value(metrics, name, labels=None):
    return metrics.registry.get_sample_value(name, labels or {})


def test_observe_request_cuenta_peticiones_y_latencia():
    metrics = Metrics()

    metrics.observe_request("GET", "/products", 200, 0.02)
    metrics.observe_request("GET", "/products", 200, 0.3)
    metrics.observe_request("POST", "/create_order", 400, 0.01)

    labels = {"method": "GET", "endpoint": "/products", "status": "200"}
    assert _value(metrics, "orderhub_http_requests_total", labels) == 2
    latency = {"method": "GET", "endpoint": "/products"}
    assert _value(metrics, "orderhub_http_request_duration_seconds_count", latency) == 2
    assert (
        _value(
            metrics,
            "orderhub_http_request_duration_seconds_bucket",
            {**latency, "le": "0.25"},
        )
        == 1
    )


def test_render_devuelve_formato_de_texto_prometheus():
    metrics = Metrics()
    metrics.orders_created.inc()

    body, content_type = metrics.render()

    assert content_type.startswith("text/plain")
    assert b"orderhub_orders_created_total 1.0" in body
    assert b"# HELP orderhub_http_requests_total" in body


def test_cada_instancia_tiene_su_propio_registro():
    first, second = Metrics(), Metrics()
    first.orders_created.inc()

    assert _value(second, "orderhub_orders_created_total") == 0


def test_metrics_notifier_cuenta_ordenes_creadas():
    metrics = Metrics()
    notifier = MetricsOrderNotifier(metrics)

    notifier.order_created(ORDER)
    notifier.order_created(ORDER)

    assert _value(metrics, "orderhub_orders_created_total") == 2


def test_composite_notifier_avisa_a_todos():
    first, second = FakeNotifier(), FakeNotifier()

    CompositeOrderNotifier([first, second]).order_created(ORDER)

    assert first.notified == second.notified == [ORDER]


def test_composite_notifier_aisla_el_fallo_de_un_notificador(caplog):
    class Broken(FakeNotifier):
        def order_created(self, order):
            raise RuntimeError("servicio de correo caído")

    after = FakeNotifier()

    CompositeOrderNotifier([Broken(), after]).order_created(ORDER)

    assert after.notified == [ORDER]
    [record] = [r for r in caplog.records if r.levelno == logging.ERROR]
    assert record.notifier == "Broken"
