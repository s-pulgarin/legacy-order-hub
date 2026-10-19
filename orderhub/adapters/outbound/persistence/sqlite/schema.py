"""Creación de tablas, datos semilla y migración de contraseñas legadas."""

from orderhub.adapters.outbound.persistence.sqlite.connection import get_connection
from orderhub.application.ports.password_hasher import PasswordHasher


def init_db(db_path: str, password_hasher: PasswordHasher) -> None:
    """Crea el esquema si no existe, carga los datos semilla y hashea contraseñas en texto plano.

    Las contraseñas semilla se guardan ya hasheadas. Si la base viene del sistema
    legado (contraseñas en claro), se migran a hash en el arranque.
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
                ("admin", password_hasher.hash("admin123"), "admin"),
                ("juan", password_hasher.hash("123456"), "client"),
            ],
        )
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
