"""Apertura de conexiones a PostgreSQL con psycopg 3."""

import psycopg
from psycopg.rows import dict_row


def get_connection(database_url: str) -> psycopg.Connection:
    """Abre una conexión a `database_url` cuyas filas se leen como diccionarios.

    psycopg abre una transacción implícita con la primera consulta; la Unit of
    Work la confirma con `commit()` o la deshace con `rollback()`.
    """
    return psycopg.connect(database_url, row_factory=dict_row)
