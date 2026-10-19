import pytest

from orderhub.application.services.auth_service import AuthService
from orderhub.domain.entities import User
from orderhub.domain.exceptions import InvalidCredentials
from tests.unit.fakes import FakeUnitOfWork


@pytest.fixture
def service():
    uow = FakeUnitOfWork(users=[User(1, "admin", "admin123", "admin")])
    return AuthService(lambda: uow)


def test_login_with_valid_credentials_returns_user(service):
    user = service.login("admin", "admin123")
    assert user.username == "admin"
    assert user.role == "admin"


@pytest.mark.parametrize("username, password", [
    ("admin", "incorrecta"),
    ("noexiste", "admin123"),
    ("' OR '1'='1", "' OR '1'='1"),
    (None, None),
    ("admin", ""),
])
def test_login_with_invalid_credentials_raises(service, username, password):
    with pytest.raises(InvalidCredentials):
        service.login(username, password)
