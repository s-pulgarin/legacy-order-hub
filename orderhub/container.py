"""Composition root: el único lugar que conoce las implementaciones concretas (Dependency Injection)."""

from dataclasses import dataclass

from orderhub.adapters.outbound.notifications.console_notifier import ConsoleOrderNotifier
from orderhub.adapters.outbound.persistence.sqlite.schema import init_db
from orderhub.adapters.outbound.persistence.sqlite.unit_of_work import SqliteUnitOfWork
from orderhub.application.services.auth_service import AuthService
from orderhub.application.services.order_service import OrderService


@dataclass
class Container:
    auth_service: AuthService
    order_service: OrderService


def build_container(db_path: str) -> Container:
    init_db(db_path)

    def uow_factory():
        return SqliteUnitOfWork(db_path)

    return Container(
        auth_service=AuthService(uow_factory),
        order_service=OrderService(uow_factory, ConsoleOrderNotifier()),
    )
