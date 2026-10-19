import logging

from flask import Flask

from orderhub.adapters.inbound.web import auth_routes, home_routes, order_routes
from orderhub.adapters.inbound.web.error_handlers import register_error_handlers
from orderhub.container import Container, build_container

DEFAULT_DB_PATH = 'orderhub.db'


def create_app(container: Container = None, secret_key: str = None) -> Flask:
    """Fábrica de la aplicación. Los tests pueden inyectar su propio `container`."""
    logging.basicConfig(level=logging.INFO)

    app = Flask(__name__, template_folder='adapters/inbound/web/templates')
    app.config['SECRET_KEY'] = secret_key
    app.extensions["orderhub"] = container or build_container(DEFAULT_DB_PATH)

    app.register_blueprint(home_routes.bp)
    app.register_blueprint(auth_routes.bp)
    app.register_blueprint(order_routes.bp)
    register_error_handlers(app)
    return app
