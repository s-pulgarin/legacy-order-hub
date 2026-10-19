"""Composition root: el único lugar que conoce las implementaciones concretas
(Dependency Injection).
"""

from dataclasses import dataclass
from typing import Iterable

from orderhub.adapters.outbound.notifications.console_notifier import (
    ConsoleOrderNotifier,
)
from orderhub.adapters.outbound.persistence.sqlite.schema import SeedUser, init_db
from orderhub.adapters.outbound.persistence.sqlite.unit_of_work import (
    SqliteUnitOfWork,
)
from orderhub.adapters.outbound.security.argon2_hasher import Argon2PasswordHasher
from orderhub.adapters.outbound.security.jwt_token_service import JWTTokenService
from orderhub.application.ports.password_hasher import PasswordHasher
from orderhub.application.ports.token_service import TokenService
from orderhub.application.services.auth_service import AuthService
from orderhub.application.services.order_service import OrderService
from orderhub.application.services.product_service import ProductService

DEFAULT_TOKEN_EXPIRES_MINUTES = 30


@dataclass
class Container:
    """Servicios de aplicación ya construidos que usan los adaptadores de entrada."""

    auth_service: AuthService
    order_service: OrderService
    product_service: ProductService


def build_container(
    db_path: str,
    secret_key: str,
    token_expires_minutes: int = DEFAULT_TOKEN_EXPIRES_MINUTES,
    password_hasher: PasswordHasher = None,
    token_service: TokenService = None,
    seed_users: Iterable[SeedUser] = (),
) -> Container:
    """Arma el grafo de dependencias: adaptadores concretos → servicios de aplicación.

    `password_hasher` y `token_service` se pueden sustituir (p. ej. en pruebas);
    por defecto se usan Argon2 y JWT. `secret_key` y `seed_users` vienen de la
    configuración del entorno (RNF-02.1), nunca del código.
    """
    password_hasher = password_hasher or Argon2PasswordHasher()
    token_service = token_service or JWTTokenService(secret_key, token_expires_minutes)
    init_db(db_path, password_hasher, seed_users)

    def uow_factory():
        """Crea una Unit of Work nueva por caso de uso (una conexión por petición)."""
        return SqliteUnitOfWork(db_path)

    return Container(
        auth_service=AuthService(uow_factory, password_hasher, token_service),
        order_service=OrderService(uow_factory, ConsoleOrderNotifier()),
        product_service=ProductService(uow_factory),
    )
