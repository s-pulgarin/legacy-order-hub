"""Puerto Unit of Work: agrupa los repositorios en una única transacción."""

from abc import ABC, abstractmethod

from orderhub.application.ports.repositories import (
    OrderRepository,
    ProductRepository,
    UserRepository,
)


class UnitOfWork(ABC):
    """Uso: `with uow: ...; uow.commit()`. Si no se llama a commit o hay una excepción, se hace rollback."""

    users: UserRepository
    products: ProductRepository
    orders: OrderRepository

    def __enter__(self) -> "UnitOfWork":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.rollback()

    @abstractmethod
    def commit(self) -> None:
        ...

    @abstractmethod
    def rollback(self) -> None:
        ...
