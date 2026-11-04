"""Punto de entrada: lee la configuración del entorno, arma la app y la arranca."""

import config
from orderhub import create_app
from orderhub.container import build_container
from orderhub.observability.logging_config import configure_logging

settings = config.load_settings()
configure_logging(settings.log_level, json_format=settings.log_json)

app = create_app(
    container=build_container(
        settings.database_path,
        settings.secret_key,
        token_expires_minutes=settings.jwt_expires_minutes,
        seed_users=settings.seed_users,
    ),
    secret_key=settings.secret_key,
)

if __name__ == "__main__":
    app.run(host=settings.host, port=settings.port, debug=settings.debug)
