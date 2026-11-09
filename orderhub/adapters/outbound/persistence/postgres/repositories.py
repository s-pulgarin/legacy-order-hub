"""Repositorios sobre PostgreSQL: implementan los mismos puertos que los de SQLite.

Todas las consultas usan parameter binding de psycopg (`%s`), nunca texto
construido con variables (RNF-02.2).
"""

from dataclasses import replace
from typing import List, Optional

import psycopg

from orderhub.application.ports.repositories import (
    OrderRepository,
    ProductRepository,
    UserRepository,
)
from orderhub.domain.entities import Order, Product, User


class PostgresUserRepository(UserRepository):
    """Implementa UserRepository sobre la tabla `users`."""

    def __init__(self, conn: psycopg.Connection):
        """Recibe la conexión de la Unit of Work en curso."""
        self._conn = conn

    def get_by_username(self, username: str) -> Optional[User]:
        """Busca un usuario por nombre."""
        row = self._conn.execute(
            "SELECT id, username, password, role FROM users WHERE username = %s",
            (username,),
        ).fetchone()
        return User(**row) if row else None

    def add(self, user: User) -> User:
        """Inserta el usuario y devuelve una copia con el id generado."""
        row = self._conn.execute(
            "INSERT INTO users (username, password, role) VALUES (%s, %s, %s)"
            " RETURNING id",
            (user.username, user.password, user.role),
        ).fetchone()
        return replace(user, id=row["id"])


class PostgresProductRepository(ProductRepository):
    """Implementa ProductRepository sobre la tabla `products`."""

    def __init__(self, conn: psycopg.Connection):
        """Recibe la conexión de la Unit of Work en curso."""
        self._conn = conn

    def get(self, product_id: int) -> Optional[Product]:
        """Busca un producto por id."""
        row = self._conn.execute(
            "SELECT id, name, price, stock FROM products WHERE id = %s",
            (product_id,),
        ).fetchone()
        return Product(**row) if row else None

    def add(self, product: Product) -> Product:
        """Inserta el producto y devuelve una copia con el id generado."""
        row = self._conn.execute(
            "INSERT INTO products (name, price, stock) VALUES (%s, %s, %s)"
            " RETURNING id",
            (product.name, product.price, product.stock),
        ).fetchone()
        return replace(product, id=row["id"])

    def list_all(self) -> List[Product]:
        """Devuelve todos los productos ordenados por id."""
        rows = self._conn.execute(
            "SELECT id, name, price, stock FROM products ORDER BY id"
        ).fetchall()
        return [Product(**row) for row in rows]

    def update_stock(self, product: Product) -> None:
        """Guarda el stock actual del producto."""
        self._conn.execute(
            "UPDATE products SET stock = %s WHERE id = %s",
            (product.stock, product.id),
        )


class PostgresOrderRepository(OrderRepository):
    """Implementa OrderRepository sobre la tabla `orders`."""

    def __init__(self, conn: psycopg.Connection):
        """Recibe la conexión de la Unit of Work en curso."""
        self._conn = conn

    def add(self, order: Order) -> Order:
        """Inserta la orden y devuelve una copia con el id generado."""
        row = self._conn.execute(
            "INSERT INTO orders (user_id, product_id, quantity, total, status)"
            " VALUES (%s, %s, %s, %s, %s) RETURNING id",
            (
                order.user_id,
                order.product_id,
                order.quantity,
                order.total,
                order.status,
            ),
        ).fetchone()
        return replace(order, id=row["id"])

    def list_all(self) -> List[Order]:
        """Devuelve todas las órdenes ordenadas por id."""
        rows = self._conn.execute(
            "SELECT id, user_id, product_id, quantity, total, status"
            " FROM orders ORDER BY id"
        ).fetchall()
        return [Order(**row) for row in rows]

    def list_by_user(self, user_id: int) -> List[Order]:
        """Devuelve las órdenes del usuario ordenadas por id."""
        rows = self._conn.execute(
            "SELECT id, user_id, product_id, quantity, total, status"
            " FROM orders WHERE user_id = %s ORDER BY id",
            (user_id,),
        ).fetchall()
        return [Order(**row) for row in rows]
