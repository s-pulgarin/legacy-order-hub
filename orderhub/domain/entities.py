"""Entidades del dominio: Python puro, sin Flask ni base de datos."""

from dataclasses import dataclass
from typing import Optional

from orderhub.domain.exceptions import InsufficientStock, InvalidInput

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
        if price <= 0:
            raise InvalidInput("El precio debe ser mayor que cero")
        if stock < 0:
            raise InvalidInput("El stock no puede ser negativo")
        return cls(id=None, name=name.strip(), price=price, stock=stock)

    def has_stock(self, quantity: int) -> bool:
        """Indica si hay unidades suficientes para vender `quantity`."""
        return self.stock >= quantity

    def decrease_stock(self, quantity: int) -> None:
        """Descuenta `quantity` unidades; lanza InsufficientStock si no alcanzan."""
        if not self.has_stock(quantity):
            raise InsufficientStock()
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
