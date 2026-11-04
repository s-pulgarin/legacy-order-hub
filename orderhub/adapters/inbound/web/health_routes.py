"""Ruta de salud para Docker, Kubernetes y Azure (sondas liveness/readiness)."""

from flask import Blueprint, jsonify

bp = Blueprint("health", __name__)


@bp.route("/healthcheck", methods=["GET"])
def healthcheck():
    """Responde 200 si el proceso atiende peticiones.

    No consulta la base de datos a propósito: si PostgreSQL tiene un problema,
    reiniciar la API no lo arregla y solo provocaría reinicios en cadena.
    """
    return jsonify({"status": "ok"}), 200
