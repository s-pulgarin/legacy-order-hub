"""Apertura de conexiones a SQLite."""

import sqlite3


def get_connection(db_path: str) -> sqlite3.Connection:
    """Abre una conexión a `db_path` cuyas filas se leen por nombre de columna."""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn
