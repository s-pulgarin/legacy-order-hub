"""Decoradores de la capa web que protegen rutas por sesión (RF-01.3) y por rol
(RF-01.4).
"""

from functools import wraps
from typing import Optional

from flask import current_app, g, request

from orderhub.domain.exceptions import AccessDenied


def _bearer_token() -> Optional[str]:
    """Extrae el token de la cabecera `Authorization: Bearer <token>`, o None si no
    está.
    """
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


def admin_required(view):
    """Exige un token válido de un usuario con rol `admin`.

    Sin token o con token inválido responde 401 (vía token_required); con un
    token válido de otro rol lanza AccessDenied, que se traduce en 403 Forbidden.
    """

    @wraps(view)
    @token_required
    def wrapper(*args, **kwargs):
        if not g.current_user.is_admin:
            raise AccessDenied()
        return view(*args, **kwargs)

    return wrapper
