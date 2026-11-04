"""Composition root: el único lugar que conoce las implementaciones concretas
(Dependency Injection).
"""

from dataclasses import dataclass
from typing import Callable, Iterable, Optional

from orderhub.adapters.outbound.notifications.composite_notifier import (
    CompositeOrderNotifier,
)
from orderhub.adapters.outbound.notifications.console_notifier import (
    ConsoleOrderNotifier,
)
from orderhub.adapters.outbound.notifications.metrics_notifier import (
    MetricsOrderNotifier,
)
from orderhub.adapters.outbound.notifications.redis_notifier import (
    RedisOrderNotifier,
)
from orderhub.adapters.outbound.persistence.postgres import schema as postgres_schema
from orderhub.adapters.outbound.persistence.postgres.unit_of_work import (
    PostgresUnitOfWork,
)
from orderhub.adapters.outbound.persistence.sqlite import schema as sqlite_schema
from orderhub.adapters.outbound.persistence.sqlite.schema import SeedUser
from orderhub.adapters.outbound.persistence.sqlite.unit_of_work import (
    SqliteUnitOfWork,
)
from orderhub.adapters.outbound.security.argon2_hasher import Argon2PasswordHasher
from orderhub.adapters.outbound.security.jwt_token_service import JWTTokenService
from orderhub.application.ports.password_hasher import PasswordHasher
from orderhub.application.ports.token_service import TokenService
from orderhub.application.ports.unit_of_work import UnitOfWork
from orderhub.application.services.auth_service import AuthService
from orderhub.application.services.order_service import OrderService
from orderhub.application.services.product_service import ProductService
from orderhub.observability.metrics import Metrics

DEFAULT_TOKEN_EXPIRES_MINUTES = 30


@dataclass
class Container:
    """Servicios de aplicación ya construidos que usan los adaptadores de entrada."""

    auth_service: AuthService
    order_service: OrderService
    product_service: ProductService
    metrics: Metrics


def build_container(
    db_path: str,
    secret_key: str,
    token_expires_minutes: int = DEFAULT_TOKEN_EXPIRES_MINUTES,
    password_hasher: PasswordHasher = None,
    token_service: TokenService = None,
    seed_users: Iterable[SeedUser] = (),
    database_url: Optional[str] = None,
    redis_client=None,
) -> Container:
    """Arma el grafo de dependencias: adaptadores concretos → servicios de aplicación.

    `password_hasher` y `token_service` se pueden sustituir (p. ej. en pruebas);
    por defecto se usan Argon2 y JWT. `secret_key` y `seed_users` vienen de la
    configuración del entorno (RNF-02.1), nunca del código.

    Persistencia: si llega `database_url` se usa PostgreSQL; si no, SQLite en
    `db_path`. Los casos de uso no notan la diferencia (mismos puertos).

    Notificación: con `redis_client` cada orden también se encola en Redis para
    que el worker la procese sin bloquear la respuesta HTTP (RF-04.1).
    """
    password_hasher = password_hasher or Argon2PasswordHasher()
    token_service = token_service or JWTTokenService(secret_key, token_expires_minutes)
    uow_factory = _persistence(db_path, database_url, password_hasher, seed_users)
    metrics = Metrics()
    notifiers = [ConsoleOrderNotifier(), MetricsOrderNotifier(metrics)]
    if redis_client is not None:
        notifiers.append(RedisOrderNotifier(redis_client))
    notifier = CompositeOrderNotifier(notifiers)

    return Container(
        auth_service=AuthService(uow_factory, password_hasher, token_service),
        order_service=OrderService(uow_factory, notifier),
        product_service=ProductService(uow_factory),
        metrics=metrics,
    )


def _persistence(
    db_path: str,
    database_url: Optional[str],
    password_hasher: PasswordHasher,
    seed_users: Iterable[SeedUser],
) -> Callable[[], UnitOfWork]:
    """Prepara la base elegida y devuelve la fábrica de Unit of Work correspondiente.

    Cada llamada a la fábrica crea una Unit of Work nueva (una conexión por caso
    de uso).
    """
    seed_users = tuple(seed_users)
    if database_url:
        postgres_schema.init_db(database_url, password_hasher, seed_users)
        return lambda: PostgresUnitOfWork(database_url)

    sqlite_schema.init_db(db_path, password_hasher, seed_users)
    return lambda: SqliteUnitOfWork(db_path)
