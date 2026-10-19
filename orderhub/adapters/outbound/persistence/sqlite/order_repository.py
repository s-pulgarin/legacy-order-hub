"""Repositorio de órdenes sobre SQLite."""

import sqlite3
from dataclasses import replace
from typing import List

from orderhub.application.ports.repositories import OrderRepository
from orderhub.domain.entities import Order


class SqliteOrderRepository(OrderRepository):
    """Implementa OrderRepository sobre la tabla `orders`."""

    def __init__(self, conn: sqlite3.Connection):
        """Recibe la conexión de la Unit of Work en curso."""
        self._conn = conn

    def add(self, order: Order) -> Order:
        """Inserta la orden y devuelve una copia con su id."""
        cursor = self._conn.execute(
            "INSERT INTO orders (user_id, product_id, quantity, total, status)"
            " VALUES (?, ?, ?, ?, ?)",
            (
                order.user_id,
                order.product_id,
                order.quantity,
                order.total,
                order.status,
            ),
        )
        return replace(order, id=cursor.lastrowid)

    def list_all(self) -> List[Order]:
        """Devuelve todas las órdenes."""
        rows = self._conn.execute(
            "SELECT id, user_id, product_id, quantity, total, status FROM orders"
        ).fetchall()
        return [Order(**dict(row)) for row in rows]
