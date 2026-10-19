"""Casos de uso de autenticación: registro e inicio de sesión (RF-01.1, RF-01.2)."""

from typing import Callable, Optional

from orderhub.application.ports.password_hasher import PasswordHasher
from orderhub.application.ports.unit_of_work import UnitOfWork
from orderhub.domain.entities import ROLE_CLIENT, User
from orderhub.domain.exceptions import (
    InvalidCredentials,
    InvalidInput,
    UserAlreadyExists,
)

MIN_PASSWORD_LENGTH = 8


class AuthService:
    """Registra usuarios y valida credenciales usando el puerto PasswordHasher."""

    def __init__(
        self,
        uow_factory: Callable[[], UnitOfWork],
        password_hasher: PasswordHasher,
    ):
        """Recibe sus dependencias por constructor (Dependency Injection)."""
        self._uow_factory = uow_factory
        self._hasher = password_hasher

    def register(self, username: Optional[str], password: Optional[str]) -> User:
        """Crea un usuario con rol `client` y guarda solo el hash de su contraseña.

        Lanza InvalidInput si faltan datos o la contraseña es corta, y
        UserAlreadyExists si el nombre ya está en uso.
        """
        username = (username or "").strip()
        if not username:
            raise InvalidInput("El nombre de usuario es obligatorio")
        if not password or len(password) < MIN_PASSWORD_LENGTH:
            raise InvalidInput(
                f"La contraseña debe tener al menos {MIN_PASSWORD_LENGTH} caracteres"
            )

        with self._uow_factory() as uow:
            if uow.users.get_by_username(username) is not None:
                raise UserAlreadyExists()
            user = uow.users.add(
                User(
                    id=None,
                    username=username,
                    password=self._hasher.hash(password),
                    role=ROLE_CLIENT,
                )
            )
            uow.commit()
        return user

    def login(self, username: Optional[str], password: Optional[str]) -> User:
        """Devuelve el usuario si las credenciales son válidas; si no, lanza InvalidCredentials."""
        if not username or not password:
            raise InvalidCredentials()

        with self._uow_factory() as uow:
            user = uow.users.get_by_username(username)

        if user is None or not self._hasher.verify(password, user.password):
            raise InvalidCredentials()
        return user
