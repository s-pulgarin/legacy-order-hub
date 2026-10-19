import sqlite3
from typing import Optional

from orderhub.application.ports.repositories import ProductRepository
from orderhub.domain.entities import Product


class SqliteProductRepository(ProductRepository):
    def __init__(self, conn: sqlite3.Connection):
        self._conn = conn

    def get(self, product_id: int) -> Optional[Product]:
        row = self._conn.execute(
            "SELECT id, name, price, stock FROM products WHERE id = ?",
            (product_id,),
        ).fetchone()
        return Product(**dict(row)) if row else None

    def update_stock(self, product: Product) -> None:
        self._conn.execute(
            "UPDATE products SET stock = ? WHERE id = ?",
            (product.stock, product.id),
        )
