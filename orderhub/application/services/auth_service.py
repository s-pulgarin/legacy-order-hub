"""Casos de uso de autenticación: registro, inicio de sesión y validación de tokens (RF-01.1 a RF-01.3)."""

from dataclasses import dataclass
from typing import Callable, Optional

from orderhub.application.ports.password_hasher import PasswordHasher
from orderhub.application.ports.token_service import TokenClaims, TokenService
from orderhub.application.ports.unit_of_work import UnitOfWork
from orderhub.domain.entities import ROLE_CLIENT, User
from orderhub.domain.exceptions import (
    InvalidCredentials,
    InvalidInput,
    InvalidToken,
    UserAlreadyExists,
)

MIN_PASSWORD_LENGTH = 8


@dataclass(frozen=True)
class AuthSession:
    """Resultado de un login exitoso: el usuario y su token de sesión."""

    user: User
    token: str
    expires_in: int


class AuthService:
    """Registra usuarios, valida credenciales y tokens usando los puertos PasswordHasher y TokenService."""

    def __init__(
        self,
        uow_factory: Callable[[], UnitOfWork],
        password_hasher: PasswordHasher,
        token_service: TokenService,
    ):
        """Recibe sus dependencias por constructor (Dependency Injection)."""
        self._uow_factory = uow_factory
        self._hasher = password_hasher
        self._tokens = token_service

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

    def login(self, username: Optional[str], password: Optional[str]) -> AuthSession:
        """Valida las credenciales y emite un token de sesión; si no son válidas, lanza InvalidCredentials."""
        if not username or not password:
            raise InvalidCredentials()

        with self._uow_factory() as uow:
            user = uow.users.get_by_username(username)

        if user is None or not self._hasher.verify(password, user.password):
            raise InvalidCredentials()
        return AuthSession(
            user=user,
            token=self._tokens.issue(user),
            expires_in=self._tokens.expires_in_seconds,
        )

    def verify_token(self, token: Optional[str]) -> TokenClaims:
        """Devuelve la identidad contenida en `token`; lanza InvalidToken si falta o no es válido."""
        if not token:
            raise InvalidToken("Se requiere un token de sesión")
        return self._tokens.verify(token)
