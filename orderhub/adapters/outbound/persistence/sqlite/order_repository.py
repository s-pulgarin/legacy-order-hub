import sqlite3
from dataclasses import replace
from typing import List

from orderhub.application.ports.repositories import OrderRepository
from orderhub.domain.entities import Order


class SqliteOrderRepository(OrderRepository):
    def __init__(self, conn: sqlite3.Connection):
        self._conn = conn

    def add(self, order: Order) -> Order:
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
        rows = self._conn.execute(
            "SELECT id, user_id, product_id, quantity, total, status FROM orders"
        ).fetchall()
        return [Order(**dict(row)) for row in rows]
