"""Backends de base de datos para las pruebas de integración.

Toda la suite de `test_api.py` corre contra SQLite (archivo temporal) y, si
está definida la variable `TEST_DATABASE_URL`, también contra PostgreSQL
(en el CI con un contenedor de servicio). Las pruebas consultan la base solo
a través de los métodos de `Backend`, sin conocer el motor.
"""

import os
import sqlite3

import psycopg
import pytest

from orderhub.adapters.outbound.persistence.postgres.repositories import (
    PostgresOrderRepository,
)
from orderhub.adapters.outbound.persistence.sqlite.order_repository import (
    SqliteOrderRepository,
)
from orderhub.container import build_container

TEST_DATABASE_URL = os.environ.get("TEST_DATABASE_URL", "").strip()


class SqliteBackend:
    """Base SQLite en un archivo temporal nuevo por prueba."""

    name = "sqlite"
    order_repository_class = SqliteOrderRepository

    def __init__(self, path):
        self.path = str(path)

    def build(self, secret, seed_users, redis_client=None):
        return build_container(
            self.path, secret, seed_users=seed_users, redis_client=redis_client
        )

    def _scalar(self, sql, params=()):
        conn = sqlite3.connect(self.path)
        try:
            return conn.execute(sql, params).fetchone()[0]
        finally:
            conn.close()

    def stock(self, product_id):
        return self._scalar("SELECT stock FROM products WHERE id = ?", (product_id,))

    def count_users(self):
        return self._scalar("SELECT COUNT(*) FROM users")

    def count_products(self):
        return self._scalar("SELECT COUNT(*) FROM products")

    def count_orders(self):
        return self._scalar("SELECT COUNT(*) FROM orders")

    def passwords(self):
        conn = sqlite3.connect(self.path)
        try:
            return [row[0] for row in conn.execute("SELECT password FROM users")]
        finally:
            conn.close()

    def create_legacy_user(self, username, plain_password, role):
        """Simula una base heredada: tabla sin restricciones y contraseña en claro."""
        conn = sqlite3.connect(self.path)
        conn.execute(
            "CREATE TABLE users (id INTEGER PRIMARY KEY AUTOINCREMENT,"
            " username TEXT, password TEXT, role TEXT)"
        )
        conn.execute(
            "INSERT INTO users (username, password, role) VALUES (?, ?, ?)",
            (username, plain_password, role),
        )
        conn.commit()
        conn.close()


class PostgresBackend:
    """Base PostgreSQL de pruebas, vaciada (tablas eliminadas) antes de cada prueba."""

    name = "postgres"
    order_repository_class = PostgresOrderRepository

    def __init__(self, url):
        self.url = url
        with psycopg.connect(url) as conn:
            conn.execute("DROP TABLE IF EXISTS orders, products, users CASCADE")

    def build(self, secret, seed_users, redis_client=None):
        return build_container(
            "unused.db",
            secret,
            seed_users=seed_users,
            database_url=self.url,
            redis_client=redis_client,
        )

    def _scalar(self, sql, params=()):
        with psycopg.connect(self.url) as conn:
            return conn.execute(sql, params).fetchone()[0]

    def stock(self, product_id):
        return self._scalar("SELECT stock FROM products WHERE id = %s", (product_id,))

    def count_users(self):
        return self._scalar("SELECT COUNT(*) FROM users")

    def count_products(self):
        return self._scalar("SELECT COUNT(*) FROM products")

    def count_orders(self):
        return self._scalar("SELECT COUNT(*) FROM orders")

    def passwords(self):
        with psycopg.connect(self.url) as conn:
            return [row[0] for row in conn.execute("SELECT password FROM users")]

    def create_legacy_user(self, username, plain_password, role):
        """Simula una base heredada: tabla sin restricciones y contraseña en claro."""
        with psycopg.connect(self.url) as conn:
            conn.execute(
                "CREATE TABLE users (id SERIAL PRIMARY KEY,"
                " username TEXT, password TEXT, role TEXT)"
            )
            conn.execute(
                "INSERT INTO users (username, password, role) VALUES (%s, %s, %s)",
                (username, plain_password, role),
            )


@pytest.fixture(params=["sqlite", "postgres"])
def backend(request, tmp_path):
    """Backend de base de datos de la prueba (PostgreSQL solo con TEST_DATABASE_URL)."""
    if request.param == "postgres":
        if not TEST_DATABASE_URL:
            pytest.skip("Define TEST_DATABASE_URL para probar contra PostgreSQL")
        return PostgresBackend(TEST_DATABASE_URL)
    return SqliteBackend(tmp_path / "test_orderhub.db")
