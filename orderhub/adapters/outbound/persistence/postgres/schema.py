"""Esquema PostgreSQL, datos semilla y migración de contraseñas en texto plano.

A diferencia del esquema SQLite heredado, aquí la base valida la integridad:
nombres de usuario únicos, claves foráneas y restricciones de stock, precio y
cantidad (TD-14).
"""

from typing import Iterable, Tuple

from orderhub.adapters.outbound.persistence.postgres.connection import get_connection
from orderhub.application.ports.password_hasher import PasswordHasher

SeedUser = Tuple[str, str, str]  # (username, contraseña en claro, rol)


def init_db(
    database_url: str,
    password_hasher: PasswordHasher,
    seed_users: Iterable[SeedUser] = (),
) -> None:
    """Crea el esquema si no existe, carga los datos semilla y hashea contraseñas.

    Igual que en SQLite: los usuarios semilla (con hash) solo se crean si la
    tabla `users` está vacía y los productos iniciales si `products` lo está.
    """
    with get_connection(database_url) as conn:
        conn.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
        username TEXT NOT NULL UNIQUE,
        password TEXT NOT NULL,
        role TEXT NOT NULL CHECK (role IN ('admin', 'client'))
    )
            """)
        conn.execute("""
    CREATE TABLE IF NOT EXISTS products (
        id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
        name TEXT NOT NULL,
        price DOUBLE PRECISION NOT NULL CHECK (price > 0),
        stock INTEGER NOT NULL CHECK (stock >= 0)
    )
            """)
        conn.execute("""
    CREATE TABLE IF NOT EXISTS orders (
        id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
        user_id INTEGER REFERENCES users (id),
        product_id INTEGER NOT NULL REFERENCES products (id),
        quantity INTEGER NOT NULL CHECK (quantity > 0),
        total DOUBLE PRECISION NOT NULL,
        status TEXT NOT NULL
    )
            """)

        if conn.execute("SELECT COUNT(*) AS n FROM users").fetchone()["n"] == 0:
            with conn.cursor() as cursor:
                cursor.executemany(
                    "INSERT INTO users (username, password, role) VALUES (%s, %s, %s)",
                    [
                        (username, password_hasher.hash(password), role)
                        for username, password, role in seed_users
                    ],
                )

        if conn.execute("SELECT COUNT(*) AS n FROM products").fetchone()["n"] == 0:
            with conn.cursor() as cursor:
                cursor.executemany(
                    "INSERT INTO products (name, price, stock) VALUES (%s, %s, %s)",
                    [("Laptop Legada", 1200.00, 5), ("Mouse USB", 15.50, 50)],
                )

        _migrate_plaintext_passwords(conn, password_hasher)


def _migrate_plaintext_passwords(conn, password_hasher: PasswordHasher) -> None:
    """Reemplaza por su hash cualquier contraseña en texto plano."""
    rows = conn.execute("SELECT id, password FROM users").fetchall()
    for row in rows:
        if not password_hasher.is_hash(row["password"]):
            conn.execute(
                "UPDATE users SET password = %s WHERE id = %s",
                (password_hasher.hash(row["password"]), row["id"]),
            )
