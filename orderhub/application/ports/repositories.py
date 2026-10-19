"""Puertos de salida para persistencia (Repository Pattern).

Los casos de uso dependen de estas interfaces; las implementaciones concretas
(SQLite hoy, PostgreSQL/SQLAlchemy mañana) viven en `adapters/outbound`.
"""

from abc import ABC, abstractmethod
from typing import List, Optional

from orderhub.domain.entities import Order, Product, User


class UserRepository(ABC):
    """Acceso a los usuarios."""

    @abstractmethod
    def get_by_username(self, username: str) -> Optional[User]:
        """Devuelve el usuario con ese nombre, o None si no existe."""

    @abstractmethod
    def add(self, user: User) -> User:
        """Persiste un usuario nuevo y lo devuelve con su `id` asignado."""


class ProductRepository(ABC):
    """Acceso al catálogo de productos."""

    @abstractmethod
    def get(self, product_id: int) -> Optional[Product]:
        """Devuelve el producto con ese id, o None si no existe."""

    @abstractmethod
    def add(self, product: Product) -> Product:
        """Persiste un producto nuevo y lo devuelve con su `id` asignado."""

    @abstractmethod
    def list_all(self) -> List[Product]:
        """Devuelve todos los productos del catálogo con su stock actual."""

    @abstractmethod
    def update_stock(self, product: Product) -> None:
        """Guarda el stock actual de `product`."""


class OrderRepository(ABC):
    """Acceso a las órdenes de compra."""

    @abstractmethod
    def add(self, order: Order) -> Order:
        """Persiste la orden y la devuelve con su `id` asignado."""

    @abstractmethod
    def list_all(self) -> List[Order]:
        """Devuelve todas las órdenes registradas."""
