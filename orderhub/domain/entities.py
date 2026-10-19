"""Entidades del dominio: Python puro, sin Flask ni base de datos."""

import math
from dataclasses import dataclass
from typing import Optional

from orderhub.domain.exceptions import InsufficientStockException, InvalidInput

ROLE_ADMIN = "admin"
ROLE_CLIENT = "client"


@dataclass
class User:
    """Usuario del sistema.

    `password` guarda siempre el hash (Argon2), nunca la contraseña en claro.
    `role` define los permisos: `admin` o `client` (RF-01.4).
    """

    id: Optional[int]
    username: str
    password: str
    role: str = ROLE_CLIENT

    @property
    def is_admin(self) -> bool:
        """Indica si el usuario puede ejecutar operaciones administrativas."""
        return self.role == ROLE_ADMIN


@dataclass
class Product:
    """Producto del catálogo con su precio unitario y stock disponible."""

    id: Optional[int]
    name: str
    price: float
    stock: int

    @classmethod
    def create(cls, name: Optional[str], price: float, stock: int) -> "Product":
        """Crea un producto nuevo validando nombre, precio y stock."""
        if not name or not name.strip():
            raise InvalidInput("El nombre del producto es obligatorio")
        if not math.isfinite(price) or price <= 0:
            raise InvalidInput("El precio debe ser mayor que cero")
        if stock < 0:
            raise InvalidInput("El stock no puede ser negativo")
        return cls(id=None, name=name.strip(), price=price, stock=stock)

    def has_stock(self, quantity: int) -> bool:
        """Indica si hay unidades suficientes para vender `quantity`."""
        return self.stock >= quantity

    def decrease_stock(self, quantity: int) -> None:
        """Descuenta `quantity` unidades del stock (RF-02.2, RF-02.3).

        Lanza InvalidInput si `quantity` no es positiva (evita aumentar el stock
        con cantidades negativas) e InsufficientStockException si
        `quantity > stock`. En ambos casos el stock no cambia.
        """
        if quantity <= 0:
            raise InvalidInput("La cantidad debe ser mayor que cero")
        if quantity > self.stock:
            raise InsufficientStockException()
        self.stock -= quantity


@dataclass
class Order:
    """Orden de compra de un producto por parte de un usuario."""

    id: Optional[int]
    user_id: Optional[int]
    product_id: int
    quantity: int
    total: float
    status: str = "PENDING"

    @classmethod
    def place(cls, user_id: Optional[int], product: Product, quantity: int) -> "Order":
        """Crea una orden para `product`, valida la cantidad y calcula el total.

        La disponibilidad de stock la valida `Product.decrease_stock`, que
        OrderService invoca antes de guardar la orden.
        """
        if quantity <= 0:
            raise InvalidInput("La cantidad debe ser mayor que cero")
        return cls(
            id=None,
            user_id=user_id,
            product_id=product.id,
            quantity=quantity,
            total=product.price * quantity,
        )
