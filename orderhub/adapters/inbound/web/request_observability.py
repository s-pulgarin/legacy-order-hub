"""Instrumentación de cada petición HTTP: request id y log estructurado (RNF-05.1)."""

import logging
import re
import uuid
from time import perf_counter

from flask import Flask, g, request

logger = logging.getLogger("orderhub.http")

# Solo se acepta un X-Request-ID entrante "limpio" (evita inyectar texto en los logs).
_REQUEST_ID_PATTERN = re.compile(r"^[A-Za-z0-9._-]{1,64}$")
UNMATCHED_ENDPOINT = "<sin_ruta>"


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


def register_request_observability(app: Flask) -> None:
    """Registra los hooks que asignan el request id y registran cada petición."""

    @app.before_request
    def start_request():
        """Asigna el request id y marca el inicio para medir la duración."""
        g.request_id = _request_id()
        g.request_started_at = perf_counter()

    @app.after_request
    def finish_request(response):
        """Devuelve el request id en la cabecera y registra la petición en JSON."""
        elapsed = perf_counter() - g.request_started_at
        response.headers["X-Request-ID"] = g.request_id
        logger.log(
            _log_level(response.status_code),
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
