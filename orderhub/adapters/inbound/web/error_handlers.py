"""Traduce las excepciones de dominio a respuestas HTTP (formato del legado)."""

import logging

from flask import jsonify
from werkzeug.exceptions import HTTPException

from orderhub.domain.exceptions import (
    AccessDenied,
    InsufficientStock,
    InvalidCredentials,
    InvalidInput,
    InvalidToken,
    ProductNotFound,
    UserAlreadyExists,
)

logger = logging.getLogger(__name__)


def register_error_handlers(app):
    """Registra en `app` un manejador por cada excepción de dominio."""

    @app.errorhandler(InvalidCredentials)
    @app.errorhandler(InvalidToken)
    def unauthorized(e):
        """401: no hay identidad válida (credenciales o token)."""
        return jsonify({"status": "error", "message": e.message}), 401

    @app.errorhandler(AccessDenied)
    def forbidden(e):
        """403: identidad válida pero sin permisos suficientes."""
        return jsonify({"status": "error", "message": e.message}), 403

    @app.errorhandler(UserAlreadyExists)
    def conflict(e):
        """409: el recurso ya existe."""
        return jsonify({"status": "error", "message": e.message}), 409

    @app.errorhandler(ProductNotFound)
    def product_not_found(e):
        """404: el producto no existe."""
        return jsonify({"error": e.message}), 404

    @app.errorhandler(InsufficientStock)
    @app.errorhandler(InvalidInput)
    def bad_request(e):
        """400: la petición no cumple las reglas de negocio."""
        return jsonify({"error": e.message}), 400

    @app.errorhandler(Exception)
    def unexpected(e):
        """500 genérico; el detalle solo va al log (el legado devolvía str(e))."""
        if isinstance(e, HTTPException):
            return e
        logger.exception("Error no controlado")
        return (
            jsonify({"status": "error", "message": "Error interno del servidor"}),
            500,
        )
