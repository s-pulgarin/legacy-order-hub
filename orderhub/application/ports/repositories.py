"""Puertos de salida para persistencia (Repository Pattern).

Los casos de uso dependen de estas interfaces; las implementaciones concretas
(SQLite hoy, PostgreSQL/SQLAlchemy mañana) viven en `adapters/outbound`.
"""

from abc import ABC, abstractmethod
from typing import List, Optional

from orderhub.domain.entities import Order, Product, User


class UserRepository(ABC):
    @abstractmethod
    def get_by_username(self, username: str) -> Optional[User]:
        ...


class ProductRepository(ABC):
    @abstractmethod
    def get(self, product_id: int) -> Optional[Product]:
        ...

    @abstractmethod
    def update_stock(self, product: Product) -> None:
        ...


class OrderRepository(ABC):
    @abstractmethod
    def add(self, order: Order) -> Order:
        """Persiste la orden y la devuelve con su `id` asignado."""

    @abstractmethod
    def list_all(self) -> List[Order]:
        ...
