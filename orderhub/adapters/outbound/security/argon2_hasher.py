"""Adaptador de PasswordHasher basado en Argon2id (librería argon2-cffi)."""

from argon2 import PasswordHasher as _Argon2
from argon2.exceptions import InvalidHashError, VerificationError

from orderhub.application.ports.password_hasher import PasswordHasher


class Argon2PasswordHasher(PasswordHasher):
    """Implementa el puerto PasswordHasher con Argon2id y los parámetros por defecto de
    argon2-cffi.
    """

    PREFIX = "$argon2"

    def __init__(self, argon2: _Argon2 = None):
        """Permite inyectar una instancia de argon2 con parámetros propios (p. ej. más
        rápidos en tests).
        """
        self._argon2 = argon2 or _Argon2()

    def hash(self, plain_password: str) -> str:
        """Genera un hash Argon2id con sal aleatoria."""
        return self._argon2.hash(plain_password)

    def verify(self, plain_password: str, password_hash: str) -> bool:
        """Compara en tiempo constante; devuelve False si no coincide o si el hash es
        inválido.
        """
        try:
            return self._argon2.verify(password_hash, plain_password)
        except (VerificationError, InvalidHashError):
            return False

    def is_hash(self, value: str) -> bool:
        """Reconoce los hashes en formato PHC de Argon2 (`$argon2id$...`)."""
        return bool(value) and value.startswith(self.PREFIX)
