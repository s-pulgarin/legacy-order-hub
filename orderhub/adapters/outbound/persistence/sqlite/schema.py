"""Creación de tablas y datos semilla (migrado desde el antiguo database.py)."""

from orderhub.adapters.outbound.persistence.sqlite.connection import get_connection


def init_db(db_path: str) -> None:
    conn = get_connection(db_path)
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT,
            password TEXT,
            role TEXT
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            price REAL,
            stock INTEGER
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            product_id INTEGER,
            quantity INTEGER,
            total REAL,
            status TEXT
        )
    ''')

    cursor.execute("SELECT COUNT(*) FROM users")
    if cursor.fetchone()[0] == 0:
        # TODO RF-01.2: guardar contraseñas con hash en lugar de texto plano.
        cursor.executemany(
            "INSERT INTO users (username, password, role) VALUES (?, ?, ?)",
            [("admin", "admin123", "admin"), ("juan", "123456", "client")],
        )
        cursor.executemany(
            "INSERT INTO products (name, price, stock) VALUES (?, ?, ?)",
            [("Laptop Legada", 1200.00, 5), ("Mouse USB", 15.50, 50)],
        )
        conn.commit()

    conn.close()
