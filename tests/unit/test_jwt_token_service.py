"""Pruebas del adaptador JWTTokenService contra la librería PyJWT real."""

from datetime import datetime, timedelta, timezone

import jwt
import pytest

from orderhub.adapters.outbound.security.jwt_token_service import JWTTokenService
from orderhub.domain.entities import User
from orderhub.domain.exceptions import InvalidToken

SECRET = "clave-de-pruebas-de-al-menos-32-bytes!!"
USER = User(7, "maria", "hash", "client")


def test_issue_y_verify_devuelven_la_identidad():
    service = JWTTokenService(SECRET, expires_minutes=30)

    claims = service.verify(service.issue(USER))

    assert (claims.user_id, claims.username, claims.role) == (7, "maria", "client")
    assert not claims.is_admin


def test_token_incluye_expiracion_configurada():
    service = JWTTokenService(SECRET, expires_minutes=15)

    payload = jwt.decode(service.issue(USER), SECRET, algorithms=["HS256"])

    assert payload["exp"] - payload["iat"] == 15 * 60
    assert service.expires_in_seconds == 900


def test_token_expirado_es_rechazado():
    hace_una_hora = datetime.now(timezone.utc) - timedelta(hours=1)
    service = JWTTokenService(SECRET, expires_minutes=30, clock=lambda: hace_una_hora)

    with pytest.raises(InvalidToken, match="expirado"):
        service.verify(service.issue(USER))


def test_token_firmado_con_otra_clave_es_rechazado():
    otro = JWTTokenService("otra-clave-distinta-de-al-menos-32-bytes")
    service = JWTTokenService(SECRET)

    with pytest.raises(InvalidToken):
        service.verify(otro.issue(USER))


def test_token_manipulado_es_rechazado():
    service = JWTTokenService(SECRET)
    header, payload, signature = service.issue(USER).split(".")

    with pytest.raises(InvalidToken):
        service.verify(f"{header}.{payload}.{signature[::-1]}")


def test_token_sin_firma_alg_none_es_rechazado():
    token = jwt.encode(
        {"sub": "1", "username": "admin", "role": "admin", "iat": 0, "exp": 9999999999},
        key=None,
        algorithm="none",
    )

    with pytest.raises(InvalidToken):
        JWTTokenService(SECRET).verify(token)


def test_clave_vacia_no_esta_permitida():
    with pytest.raises(ValueError):
        JWTTokenService("")
