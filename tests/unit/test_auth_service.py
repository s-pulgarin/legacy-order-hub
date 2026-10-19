"""Pruebas unitarias de AuthService (RF-01.1 a RF-01.3) con adaptadores falsos en memoria."""

import pytest

from orderhub.application.services.auth_service import AuthService
from orderhub.domain.entities import User
from orderhub.domain.exceptions import (
    InvalidCredentials,
    InvalidInput,
    InvalidToken,
    UserAlreadyExists,
)
from tests.unit.fakes import FakePasswordHasher, FakeTokenService, FakeUnitOfWork


@pytest.fixture
def hasher():
    return FakePasswordHasher()


@pytest.fixture
def uow(hasher):
    admin = User(1, "admin", hasher.hash("admin123"), "admin")
    return FakeUnitOfWork(users=[admin])


@pytest.fixture
def service(uow, hasher):
    return AuthService(lambda: uow, hasher, FakeTokenService())


# --- Login: caso exitoso -------------------------------------------------


def test_login_exitoso_devuelve_usuario_y_token(service):
    session = service.login("admin", "admin123")

    assert session.user.username == "admin"
    assert session.user.role == "admin"
    assert session.token == "token:1:admin:admin"
    assert session.expires_in == 1800


# --- Login: casos fallidos -----------------------------------------------


def test_login_fallido_con_contrasena_incorrecta_lanza_invalid_credentials(service):
    with pytest.raises(InvalidCredentials):
        service.login("admin", "contrasena-incorrecta")


@pytest.mark.parametrize(
    "username, password",
    [
        ("noexiste", "admin123"),
        ("' OR '1'='1", "' OR '1'='1"),
        (None, None),
        ("admin", ""),
        ("admin", "hashed:admin123"),  # enviar el hash no sirve como contraseña
    ],
)
def test_login_fallido_con_credenciales_invalidas(service, username, password):
    with pytest.raises(InvalidCredentials):
        service.login(username, password)


# --- Registro --------------------------------------------------------------


def test_register_guarda_hash_y_rol_client(service, uow):
    user = service.register("maria", "secreta123")

    assert user.id is not None
    assert user.role == "client"
    assert user.password == "hashed:secreta123"
    assert uow.users.get_by_username("maria").password != "secreta123"
    assert uow.committed


def test_register_permite_login_posterior(service):
    service.register("maria", "secreta123")

    assert service.login("maria", "secreta123").user.username == "maria"


def test_register_usuario_duplicado_lanza_user_already_exists(service):
    with pytest.raises(UserAlreadyExists):
        service.register("admin", "otraclave123")


@pytest.mark.parametrize(
    "username, password", [("", "secreta123"), ("maria", "corta"), ("maria", None)]
)
def test_register_con_datos_invalidos_lanza_invalid_input(service, username, password):
    with pytest.raises(InvalidInput):
        service.register(username, password)


# --- Validación de token -----------------------------------------------------


def test_verify_token_devuelve_la_identidad(service):
    token = service.login("admin", "admin123").token

    claims = service.verify_token(token)

    assert (claims.user_id, claims.username, claims.is_admin) == (1, "admin", True)


@pytest.mark.parametrize("token", [None, "", "basura"])
def test_verify_token_invalido_lanza_invalid_token(service, token):
    with pytest.raises(InvalidToken):
        service.verify_token(token)
