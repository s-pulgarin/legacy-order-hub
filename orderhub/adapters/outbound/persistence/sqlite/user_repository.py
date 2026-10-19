import sqlite3
from typing import Optional

from orderhub.application.ports.repositories import UserRepository
from orderhub.domain.entities import User


class SqliteUserRepository(UserRepository):
    def __init__(self, conn: sqlite3.Connection):
        self._conn = conn

    def get_by_username(self, username: str) -> Optional[User]:
        # Consulta parametrizada: elimina la inyección SQL del /login legado.
        row = self._conn.execute(
            "SELECT id, username, password, role FROM users WHERE username = ?",
            (username,),
        ).fetchone()
        return User(**dict(row)) if row else None
