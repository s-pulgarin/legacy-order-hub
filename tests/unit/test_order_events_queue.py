"""Pruebas de la notificación asíncrona por Redis (RF-04.1) con fakeredis."""

import json
import logging
import threading

import fakeredis
import pytest

from orderhub.adapters.inbound.queue.order_events_worker import (
    OrderEventsWorker,
    send_confirmation_email,
)
from orderhub.adapters.outbound.notifications.redis_notifier import (
    ORDER_EVENTS_QUEUE,
    RedisOrderNotifier,
)
from orderhub.domain.entities import Order

ORDER = Order(7, 2, 1, 3, 3600.0)


@pytest.fixture
def redis_client():
    return fakeredis.FakeRedis(decode_responses=True)


def test_notifier_encola_el_evento_en_json(redis_client):
    RedisOrderNotifier(redis_client).order_created(ORDER)

    [raw] = redis_client.lrange(ORDER_EVENTS_QUEUE, 0, -1)
    event = json.loads(raw)
    assert event["event"] == "order_created"
    assert (event["order_id"], event["user_id"], event["total"]) == (7, 2, 3600.0)
    assert event["occurred_at"].endswith("+00:00")


def test_worker_procesa_los_eventos_en_orden_de_llegada(redis_client):
    notifier = RedisOrderNotifier(redis_client)
    processed = []
    worker = OrderEventsWorker(redis_client, handler=processed.append, poll_timeout=1)

    notifier.order_created(ORDER)
    notifier.order_created(Order(8, 2, 1, 1, 1200.0))

    assert worker.process_next() and worker.process_next()
    assert [e["order_id"] for e in processed] == [7, 8]
    assert redis_client.llen(ORDER_EVENTS_QUEUE) == 0


def test_worker_sin_mensajes_devuelve_false(redis_client):
    worker = OrderEventsWorker(redis_client, handler=lambda e: None, poll_timeout=1)
    assert worker.process_next() is False


def test_mensaje_invalido_se_descarta_y_se_registra(redis_client, caplog):
    redis_client.lpush(ORDER_EVENTS_QUEUE, "esto no es json")
    processed = []

    OrderEventsWorker(redis_client, handler=processed.append).process_next()

    assert processed == []
    assert any(r.levelno == logging.ERROR for r in caplog.records)


def test_si_el_handler_falla_el_mensaje_va_a_la_cola_de_fallidos(redis_client):
    def broken(event):
        raise RuntimeError("proveedor de correo caído")

    RedisOrderNotifier(redis_client).order_created(ORDER)

    OrderEventsWorker(redis_client, handler=broken).process_next()

    [failed] = redis_client.lrange(ORDER_EVENTS_QUEUE + ":failed", 0, -1)
    assert json.loads(failed)["order_id"] == 7


def test_run_se_detiene_con_la_senal_de_parada(redis_client):
    stop = threading.Event()
    processed = []

    def handle_and_stop(event):
        processed.append(event)
        stop.set()

    RedisOrderNotifier(redis_client).order_created(ORDER)
    OrderEventsWorker(redis_client, handler=handle_and_stop, poll_timeout=1).run(stop)

    assert [e["order_id"] for e in processed] == [7]


def test_envio_de_correo_simulado_deja_constancia_en_el_log(caplog):
    caplog.set_level("INFO")

    send_confirmation_email({"order_id": 7, "user_id": 2, "total": 10.0})

    [record] = caplog.records
    assert record.event == "order_confirmation_sent"
    assert record.order_id == 7
