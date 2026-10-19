"""Caso de uso de autenticación (RF-01.1)."""

import hmac
from typing import Callable, Optional

from orderhub.application.ports.unit_of_work import UnitOfWork
from orderhub.domain.entities import User
from orderhub.domain.exceptions import InvalidCredentials


class AuthService:
    def __init__(self, uow_factory: Callable[[], UnitOfWork]):
        self._uow_factory = uow_factory

    def login(self, username: Optional[str], password: Optional[str]) -> User:
        """Devuelve el usuario si las credenciales son válidas; si no, lanza InvalidCredentials."""
        if not username or not password:
            raise InvalidCredentials()

        with self._uow_factory() as uow:
            user = uow.users.get_by_username(username)

        if user is None or not self._password_matches(password, user.password):
            raise InvalidCredentials()
        return user

    @staticmethod
    def _password_matches(plain: str, stored: str) -> bool:
        # TODO RF-01.2: reemplazar por un puerto PasswordHasher (bcrypt/argon2).
        return hmac.compare_digest(plain.encode(), (stored or "").encode())
