"""Ruta `/metrics` para que Prometheus recolecte las métricas (RNF-05.2)."""

from flask import Blueprint, Response, current_app

bp = Blueprint("metrics", __name__)


@bp.route("/metrics", methods=["GET"])
def metrics():
    """Expone las métricas en el formato de texto de Prometheus."""
    body, content_type = current_app.extensions["orderhub"].metrics.render()
    return Response(body, content_type=content_type)
