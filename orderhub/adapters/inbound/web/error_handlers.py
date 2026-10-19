"""Traduce las excepciones de dominio a respuestas HTTP (mismo formato que el legado)."""

import logging

from flask import jsonify
from werkzeug.exceptions import HTTPException

from orderhub.domain.exceptions import (
    InsufficientStock,
    InvalidCredentials,
    InvalidInput,
    ProductNotFound,
)

logger = logging.getLogger(__name__)


def register_error_handlers(app):
    @app.errorhandler(InvalidCredentials)
    def invalid_credentials(e):
        return jsonify({"status": "error", "message": e.message}), 401

    @app.errorhandler(ProductNotFound)
    def product_not_found(e):
        return jsonify({"error": e.message}), 404

    @app.errorhandler(InsufficientStock)
    @app.errorhandler(InvalidInput)
    def bad_request(e):
        return jsonify({"error": e.message}), 400

    @app.errorhandler(Exception)
    def unexpected(e):
        if isinstance(e, HTTPException):
            return e
        # El legado devolvía str(e) al cliente; ahora el detalle solo va al log.
        logger.exception("Error no controlado")
        return jsonify({"status": "error", "message": "Error interno del servidor"}), 500
