"""Pruebas de los logs estructurados en JSON (RNF-05.1)."""

import io
import json
import logging

import pytest
from flask import Flask, g

from orderhub.application.ports.token_service import TokenClaims
from orderhub.observability.logging_config import configure_logging


@pytest.fixture
def restore_root_logger():
    """Deja el logger raíz como estaba (configure_logging lo modifica)."""
    root = logging.getLogger()
    handlers, level = root.handlers[:], root.level
    yield
    root.handlers, root.level = handlers, level


def _lines(stream):
    return [json.loads(line) for line in stream.getvalue().splitlines()]


def test_cada_registro_es_json_con_timestamp_nivel_y_contexto(restore_root_logger):
    stream = io.StringIO()
    configure_logging("INFO", json_format=True, stream=stream)

    logging.getLogger("orderhub.prueba").warning(
        "Stock bajo", extra={"product_id": 1, "stock": 2}
    )

    [record] = _lines(stream)
    assert record["message"] == "Stock bajo"
    assert record["level"] == "WARNING"
    assert record["logger"] == "orderhub.prueba"
    assert record["timestamp"].endswith("+00:00")  # ISO 8601 en UTC
    assert (record["product_id"], record["stock"]) == (1, 2)


def test_las_tildes_se_escriben_sin_escapar(restore_root_logger):
    stream = io.StringIO()
    configure_logging("INFO", json_format=True, stream=stream)

    logging.getLogger("orderhub.prueba").info("Petición atendida")

    assert "Petición atendida" in stream.getvalue()


def test_respeta_el_nivel_configurado(restore_root_logger):
    stream = io.StringIO()
    configure_logging("WARNING", json_format=True, stream=stream)

    logging.getLogger("orderhub.prueba").info("no debe salir")

    assert stream.getvalue() == ""


def test_formato_texto_para_desarrollo(restore_root_logger):
    stream = io.StringIO()
    configure_logging("INFO", json_format=False, stream=stream)

    logging.getLogger("orderhub.prueba").info("hola")

    assert "INFO [orderhub.prueba] hola" in stream.getvalue()


def test_las_excepciones_incluyen_la_traza(restore_root_logger):
    stream = io.StringIO()
    configure_logging("INFO", json_format=True, stream=stream)

    try:
        raise RuntimeError("fallo")
    except RuntimeError:
        logging.getLogger("orderhub.prueba").exception("Error no controlado")

    [record] = _lines(stream)
    assert record["level"] == "ERROR"
    assert "RuntimeError: fallo" in record["exc_info"]


def test_dentro_de_una_peticion_agrega_request_id_y_user_id(restore_root_logger):
    stream = io.StringIO()
    configure_logging("INFO", json_format=True, stream=stream)
    app = Flask(__name__)

    with app.test_request_context("/"):
        g.request_id = "abc123"
        g.current_user = TokenClaims(7, "maria", "client")
        logging.getLogger("orderhub.prueba").info("dentro")
    logging.getLogger("orderhub.prueba").info("fuera")

    dentro, fuera = _lines(stream)
    assert (dentro["request_id"], dentro["user_id"]) == ("abc123", 7)
    assert "request_id" not in fuera


def test_nivel_invalido_lanza_error(restore_root_logger):
    with pytest.raises(ValueError):
        configure_logging("VERBOSE")
