"""Repositorio de productos sobre SQLite."""

import sqlite3
from dataclasses import replace
from typing import List, Optional

from orderhub.application.ports.repositories import ProductRepository
from orderhub.domain.entities import Product


class SqliteProductRepository(ProductRepository):
    """Implementa ProductRepository con consultas parametrizadas sobre la tabla
    `products`.
    """

    def __init__(self, conn: sqlite3.Connection):
        """Recibe la conexión de la Unit of Work en curso."""
        self._conn = conn

    def get(self, product_id: int) -> Optional[Product]:
        """Busca un producto por id."""
        row = self._conn.execute(
            "SELECT id, name, price, stock FROM products WHERE id = ?",
            (product_id,),
        ).fetchone()
        return Product(**dict(row)) if row else None

    def add(self, product: Product) -> Product:
        """Inserta el producto y devuelve una copia con su id."""
        cursor = self._conn.execute(
            "INSERT INTO products (name, price, stock) VALUES (?, ?, ?)",
            (product.name, product.price, product.stock),
        )
        return replace(product, id=cursor.lastrowid)

    def list_all(self) -> List[Product]:
        """Devuelve todos los productos ordenados por id."""
        rows = self._conn.execute(
            "SELECT id, name, price, stock FROM products ORDER BY id"
        ).fetchall()
        return [Product(**dict(row)) for row in rows]

    def update_stock(self, product: Product) -> None:
        """Guarda el stock actual del producto."""
        self._conn.execute(
            "UPDATE products SET stock = ? WHERE id = ?",
            (product.stock, product.id),
        )
