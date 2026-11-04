"""Logs estructurados en formato JSON (RNF-05.1).

Cada registro sale como una línea JSON con marca de tiempo ISO 8601 en UTC,
nivel de severidad, logger, mensaje y contexto: el `request_id` y el
`user_id` de la petición en curso, más los campos que se pasen en `extra`.
"""

import logging
import sys
from typing import IO, Optional

from flask import g, has_request_context
from pythonjsonlogger.json import JsonFormatter

VALID_LEVELS = ("DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL")


class RequestContextFilter(logging.Filter):
    """Añade `request_id` y `user_id` a los registros emitidos durante una petición."""

    def filter(self, record: logging.LogRecord) -> bool:
        """Completa el registro con el contexto de Flask; nunca lo descarta."""
        if has_request_context():
            if not hasattr(record, "request_id"):
                record.request_id = getattr(g, "request_id", None)
            user = getattr(g, "current_user", None)
            if user is not None and not hasattr(record, "user_id"):
                record.user_id = user.user_id
        return True


def build_formatter(json_format: bool) -> logging.Formatter:
    """Devuelve el formateador JSON o, para leer en desarrollo, uno de texto."""
    if json_format:
        return JsonFormatter(
            "{levelname}{name}{message}",
            style="{",
            rename_fields={"levelname": "level", "name": "logger"},
            timestamp=True,
            json_ensure_ascii=False,
        )
    return logging.Formatter("%(asctime)s %(levelname)s [%(name)s] %(message)s")


def configure_logging(
    level: str = "INFO", json_format: bool = True, stream: Optional[IO[str]] = None
) -> logging.Handler:
    """Configura el logger raíz con un solo handler hacia `stream` (o stdout).

    Escribir a stdout es lo esperado en contenedores: Docker, Kubernetes y
    Azure recogen esa salida. Silencia el log de acceso de Werkzeug porque
    cada petición ya se registra en JSON (ver `request_observability`).
    Devuelve el handler creado (útil en pruebas).
    """
    if level not in VALID_LEVELS:
        raise ValueError(f"Nivel de log inválido: {level}")

    handler = logging.StreamHandler(stream or sys.stdout)
    handler.setFormatter(build_formatter(json_format))
    handler.addFilter(RequestContextFilter())

    root = logging.getLogger()
    root.handlers = [handler]
    root.setLevel(level)
    logging.getLogger("werkzeug").setLevel(logging.WARNING)
    return handler
