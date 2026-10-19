"""Creación de tablas, datos semilla y migración de contraseñas legadas."""

from typing import Iterable, Tuple

from orderhub.adapters.outbound.persistence.sqlite.connection import get_connection
from orderhub.application.ports.password_hasher import PasswordHasher

SeedUser = Tuple[str, str, str]  # (username, contraseña en claro, rol)


def init_db(
    db_path: str,
    password_hasher: PasswordHasher,
    seed_users: Iterable[SeedUser] = (),
) -> None:
    """Crea el esquema, carga los datos semilla y hashea contraseñas en texto plano.

    `seed_users` llega desde la configuración (variables SEED_*_PASSWORD del
    entorno), así que ninguna contraseña está escrita en el código. Los usuarios
    se crean, con su contraseña hasheada, solo si la tabla `users` está vacía.
    Si la base viene del sistema legado (contraseñas en claro), se migran a hash.
    """
    conn = get_connection(db_path)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT,
            password TEXT,
            role TEXT
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            price REAL,
            stock INTEGER
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            product_id INTEGER,
            quantity INTEGER,
            total REAL,
            status TEXT
        )
    """)

    cursor.execute("SELECT COUNT(*) FROM users")
    if cursor.fetchone()[0] == 0:
        cursor.executemany(
            "INSERT INTO users (username, password, role) VALUES (?, ?, ?)",
            [
                (username, password_hasher.hash(password), role)
                for username, password, role in seed_users
            ],
        )

    cursor.execute("SELECT COUNT(*) FROM products")
    if cursor.fetchone()[0] == 0:
        cursor.executemany(
            "INSERT INTO products (name, price, stock) VALUES (?, ?, ?)",
            [("Laptop Legada", 1200.00, 5), ("Mouse USB", 15.50, 50)],
        )

    _migrate_plaintext_passwords(cursor, password_hasher)
    conn.commit()
    conn.close()


def _migrate_plaintext_passwords(cursor, password_hasher: PasswordHasher) -> None:
    """Reemplaza por su hash cualquier contraseña heredada en texto plano."""
    rows = cursor.execute("SELECT id, password FROM users").fetchall()
    for row in rows:
        if row["password"] and not password_hasher.is_hash(row["password"]):
            cursor.execute(
                "UPDATE users SET password = ? WHERE id = ?",
                (password_hasher.hash(row["password"]), row["id"]),
            )
