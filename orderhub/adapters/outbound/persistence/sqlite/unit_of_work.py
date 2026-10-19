"""Unit of Work sobre SQLite: agrupa los repositorios en una transacción."""

from orderhub.adapters.outbound.persistence.sqlite.connection import get_connection
from orderhub.adapters.outbound.persistence.sqlite.order_repository import (
    SqliteOrderRepository,
)
from orderhub.adapters.outbound.persistence.sqlite.product_repository import (
    SqliteProductRepository,
)
from orderhub.adapters.outbound.persistence.sqlite.user_repository import (
    SqliteUserRepository,
)
from orderhub.application.ports.unit_of_work import UnitOfWork


class SqliteUnitOfWork(UnitOfWork):
    """Una conexión y una transacción por caso de uso; se crea una instancia nueva por
    petición.
    """

    def __init__(self, db_path: str):
        """Guarda la ruta de la base; la conexión se abre al entrar en el `with`."""
        self._db_path = db_path
        self._conn = None

    def __enter__(self) -> "SqliteUnitOfWork":
        """Abre la conexión y crea los repositorios que la comparten."""
        self._conn = get_connection(self._db_path)
        self.users = SqliteUserRepository(self._conn)
        self.products = SqliteProductRepository(self._conn)
        self.orders = SqliteOrderRepository(self._conn)
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
