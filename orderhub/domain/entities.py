"""Entidades del dominio: Python puro, sin Flask ni base de datos."""

from dataclasses import dataclass
from typing import Optional

from orderhub.domain.exceptions import InsufficientStock, InvalidInput


@dataclass
class User:
    id: Optional[int]
    username: str
    password: str
    role: str


@dataclass
class Product:
    id: Optional[int]
    name: str
    price: float
    stock: int

    def has_stock(self, quantity: int) -> bool:
        return self.stock >= quantity

    def decrease_stock(self, quantity: int) -> None:
        if not self.has_stock(quantity):
            raise InsufficientStock()
        self.stock -= quantity


@dataclass
class Order:
    id: Optional[int]
    user_id: Optional[int]
    product_id: int
    quantity: int
    total: float
    status: str = "PENDING"

    @classmethod
    def place(cls, user_id: Optional[int], product: Product, quantity: int) -> "Order":
        """Crea una orden nueva para `product`, valida la cantidad y calcula el total."""
        if quantity <= 0:
            raise InvalidInput("La cantidad debe ser mayor que cero")
        if not product.has_stock(quantity):
            raise InsufficientStock()
        return cls(
            id=None,
            user_id=user_id,
            product_id=product.id,
            quantity=quantity,
            total=product.price * quantity,
        )
