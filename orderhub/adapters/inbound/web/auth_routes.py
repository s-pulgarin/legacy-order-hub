"""Rutas HTTP de autenticación: registro e inicio de sesión."""

from flask import Blueprint, current_app, jsonify, request

from orderhub.adapters.inbound.web.serializers import user_to_dict

bp = Blueprint("auth", __name__)


def _auth_service():
    """Obtiene el AuthService inyectado en la aplicación."""
    return current_app.extensions["orderhub"].auth_service


@bp.route("/register", methods=["POST"])
def register():
    """Registra un usuario con rol `client`. 201 si se crea; 400 o 409 si no."""
    data = request.get_json(silent=True) or {}
    user = _auth_service().register(data.get("username"), data.get("password"))
    return jsonify({"status": "success", "user": user_to_dict(user)}), 201


@bp.route("/login", methods=["POST"])
def login():
    """Valida usuario y contraseña. 200 con el usuario; 401 si las credenciales no son válidas."""
    data = request.get_json(silent=True) or {}
    user = _auth_service().login(data.get("username"), data.get("password"))
    return jsonify({"status": "success", "user": user_to_dict(user)}), 200
