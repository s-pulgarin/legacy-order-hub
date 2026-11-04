"""Unit of Work sobre PostgreSQL: agrupa los repositorios en una transacción."""

from orderhub.adapters.outbound.persistence.postgres.connection import get_connection
from orderhub.adapters.outbound.persistence.postgres.repositories import (
    PostgresOrderRepository,
    PostgresProductRepository,
    PostgresUserRepository,
)
from orderhub.application.ports.unit_of_work import UnitOfWork


class PostgresUnitOfWork(UnitOfWork):
    """Una conexión y una transacción por caso de uso (una instancia por petición)."""

    def __init__(self, database_url: str):
        """Guarda la URL; la conexión se abre al entrar en el `with`."""
        self._database_url = database_url
        self._conn = None

    def __enter__(self) -> "PostgresUnitOfWork":
        """Abre la conexión y crea los repositorios que la comparten."""
        self._conn = get_connection(self._database_url)
        self.users = PostgresUserRepository(self._conn)
        self.products = PostgresProductRepository(self._conn)
        self.orders = PostgresOrderRepository(self._conn)
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        """Deshace lo no confirmado y cierra la conexión, haya o no excepción."""
        super().__exit__(exc_type, exc, tb)
        self._conn.close()

    def commit(self) -> None:
        """Confirma la transacción en curso."""
        self._conn.commit()

    def rollback(self) -> None:
        """Deshace los cambios no confirmados."""
        self._conn.rollback()
