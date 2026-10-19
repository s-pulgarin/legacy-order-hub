"""Paquete principal de OrderHub: expone la fábrica de la aplicación Flask."""

import logging

from flask import Flask

from orderhub.adapters.inbound.web import (
    auth_routes,
    home_routes,
    order_routes,
    product_routes,
)
from orderhub.adapters.inbound.web.error_handlers import register_error_handlers
from orderhub.container import Container


def create_app(container: Container, secret_key: str) -> Flask:
    """Fábrica de la aplicación Flask.

    Recibe el `container` ya armado (ver `app.py` y `build_container`) y la
    `secret_key` leída del entorno; no tiene valores por defecto ocultos.
    """
    logging.basicConfig(level=logging.INFO)

    app = Flask(__name__, template_folder="adapters/inbound/web/templates")
    app.config["SECRET_KEY"] = secret_key
    app.extensions["orderhub"] = container

    app.register_blueprint(home_routes.bp)
    app.register_blueprint(auth_routes.bp)
    app.register_blueprint(order_routes.bp)
    app.register_blueprint(product_routes.bp)
    register_error_handlers(app)
    return app
