"""Repositorio de usuarios sobre SQLite."""

import sqlite3
from dataclasses import replace
from typing import Optional

from orderhub.application.ports.repositories import UserRepository
from orderhub.domain.entities import User


class SqliteUserRepository(UserRepository):
    """Implementa UserRepository con consultas parametrizadas sobre la tabla `users`."""

    def __init__(self, conn: sqlite3.Connection):
        """Recibe la conexión de la Unit of Work en curso."""
        self._conn = conn

    def get_by_username(self, username: str) -> Optional[User]:
        """Busca por nombre; la consulta parametrizada elimina la inyección SQL del /login legado."""
        row = self._conn.execute(
            "SELECT id, username, password, role FROM users WHERE username = ?",
            (username,),
        ).fetchone()
        return User(**dict(row)) if row else None

    def add(self, user: User) -> User:
        """Inserta el usuario (con la contraseña ya hasheada) y devuelve una copia con su id."""
        cursor = self._conn.execute(
            "INSERT INTO users (username, password, role) VALUES (?, ?, ?)",
            (user.username, user.password, user.role),
        )
        return replace(user, id=cursor.lastrowid)
