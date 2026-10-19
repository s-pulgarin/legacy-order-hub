"""Decoradores de la capa web que protegen rutas con el token de sesión (RF-01.3)."""

from functools import wraps
from typing import Optional

from flask import current_app, g, request


def _bearer_token() -> Optional[str]:
    """Extrae el token de la cabecera `Authorization: Bearer <token>`, o None si no está."""
    scheme, _, token = request.headers.get("Authorization", "").partition(" ")
    if scheme.lower() != "bearer" or not token.strip():
        return None
    return token.strip()


def token_required(view):
    """Exige un token válido; deja la identidad en `g.current_user` (TokenClaims).

    Si el token falta, está mal formado o expiró, AuthService lanza InvalidToken
    y el manejador de errores responde 401.
    """

    @wraps(view)
    def wrapper(*args, **kwargs):
        auth_service = current_app.extensions["orderhub"].auth_service
        g.current_user = auth_service.verify_token(_bearer_token())
        return view(*args, **kwargs)

    return wrapper
