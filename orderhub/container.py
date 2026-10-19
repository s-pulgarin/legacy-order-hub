"""Composition root: el único lugar que conoce las implementaciones concretas (Dependency Injection)."""

from dataclasses import dataclass

from orderhub.adapters.outbound.notifications.console_notifier import (
    ConsoleOrderNotifier,
)
from orderhub.adapters.outbound.persistence.sqlite.schema import init_db
from orderhub.adapters.outbound.persistence.sqlite.unit_of_work import (
    SqliteUnitOfWork,
)
from orderhub.adapters.outbound.security.argon2_hasher import Argon2PasswordHasher
from orderhub.application.ports.password_hasher import PasswordHasher
from orderhub.application.services.auth_service import AuthService
from orderhub.application.services.order_service import OrderService


@dataclass
class Container:
    """Servicios de aplicación ya construidos que usan los adaptadores de entrada."""

    auth_service: AuthService
    order_service: OrderService


def build_container(db_path: str, password_hasher: PasswordHasher = None) -> Container:
    """Arma el grafo de dependencias: adaptadores concretos → servicios de aplicación."""
    password_hasher = password_hasher or Argon2PasswordHasher()
    init_db(db_path, password_hasher)

    def uow_factory():
        """Crea una Unit of Work nueva por caso de uso (una conexión por petición)."""
        return SqliteUnitOfWork(db_path)

    return Container(
        auth_service=AuthService(uow_factory, password_hasher),
        order_service=OrderService(uow_factory, ConsoleOrderNotifier()),
    )
