"""Instrumentación de cada petición HTTP: request id, log JSON (RNF-05.1) y
métricas RED (RNF-05.2)."""

import logging
import re
import uuid
from time import perf_counter

from typing import Optional

from flask import Flask, g, request

from orderhub.observability.metrics import Metrics

logger = logging.getLogger("orderhub.http")

# Solo se acepta un X-Request-ID entrante "limpio" (evita inyectar texto en los logs).
_REQUEST_ID_PATTERN = re.compile(r"^[A-Za-z0-9._-]{1,64}$")
UNMATCHED_ENDPOINT = "<sin_ruta>"
# Rutas de infraestructura que se consultan cada pocos segundos (Prometheus y las
# sondas de salud): no alimentan las métricas RED y se registran solo en DEBUG.
UNMEASURED_ENDPOINTS = {"/metrics", "/healthcheck"}


def _request_id() -> str:
    """Reutiliza el X-Request-ID del cliente si es válido; si no, genera uno nuevo."""
    incoming = request.headers.get("X-Request-ID", "")
    if _REQUEST_ID_PATTERN.match(incoming):
        return incoming
    return uuid.uuid4().hex


def endpoint_label() -> str:
    """Ruta registrada (p. ej. `/products`) en lugar de la URL real: acota etiquetas."""
    return request.url_rule.rule if request.url_rule else UNMATCHED_ENDPOINT


def _log_level(status: int) -> int:
    """ERROR para 5xx, WARNING para 4xx e INFO para el resto."""
    if status >= 500:
        return logging.ERROR
    if status >= 400:
        return logging.WARNING
    return logging.INFO


def register_request_observability(app: Flask, metrics: Optional[Metrics] = None):
    """Registra los hooks que asignan el request id, registran cada petición en
    el log y, si se pasan `metrics`, alimentan las métricas RED.
    """

    @app.before_request
    def start_request():
        """Asigna el request id y marca el inicio para medir la duración."""
        g.request_id = _request_id()
        g.request_started_at = perf_counter()
        g.measured = (
            metrics is not None and endpoint_label() not in UNMEASURED_ENDPOINTS
        )
        if g.measured:
            metrics.http_requests_in_progress.inc()

    @app.after_request
    def finish_request(response):
        """Devuelve el request id en la cabecera y registra la petición en JSON."""
        elapsed = perf_counter() - g.request_started_at
        response.headers["X-Request-ID"] = g.request_id
        if g.measured:
            metrics.observe_request(
                request.method, endpoint_label(), response.status_code, elapsed
            )
        quiet = endpoint_label() in UNMEASURED_ENDPOINTS
        logger.log(
            logging.DEBUG if quiet else _log_level(response.status_code),
            "Petición HTTP atendida",
            extra={
                "method": request.method,
                "path": request.path,
                "endpoint": endpoint_label(),
                "status": response.status_code,
                "duration_ms": round(elapsed * 1000, 2),
                "remote_addr": request.remote_addr,
            },
        )
        return response

    @app.teardown_request
    def end_request(_error):
        """Baja el contador de peticiones en curso, incluso si hubo una excepción."""
        if getattr(g, "measured", False):
            metrics.http_requests_in_progress.dec()
