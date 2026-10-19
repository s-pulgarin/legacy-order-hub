"""Puerto de salida para el hashing de contraseñas (RF-01.2)."""

from abc import ABC, abstractmethod


class PasswordHasher(ABC):
    """Calcula y verifica hashes de contraseñas sin acoplar el núcleo a un algoritmo concreto."""

    @abstractmethod
    def hash(self, plain_password: str) -> str:
        """Devuelve el hash de `plain_password`, listo para guardarse en la base de datos."""

    @abstractmethod
    def verify(self, plain_password: str, password_hash: str) -> bool:
        """Indica si `plain_password` corresponde a `password_hash`. Nunca lanza por un hash inválido."""

    @abstractmethod
    def is_hash(self, value: str) -> bool:
        """Indica si `value` ya es un hash de este algoritmo (sirve para migrar contraseñas legadas)."""
