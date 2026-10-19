"""Puerto de salida para emitir y validar tokens de sesión (RF-01.3)."""

from abc import ABC, abstractmethod
from dataclasses import dataclass

from orderhub.domain.entities import ROLE_ADMIN, User


@dataclass(frozen=True)
class TokenClaims:
    """Identidad del usuario autenticado, extraída de un token válido."""

    user_id: int
    username: str
    role: str

    @property
    def is_admin(self) -> bool:
        """Indica si el portador del token tiene rol admin."""
        return self.role == ROLE_ADMIN


class TokenService(ABC):
    """Emite tokens firmados con expiración y los valida."""

    expires_in_seconds: int

    @abstractmethod
    def issue(self, user: User) -> str:
        """Genera un token firmado para `user` que expira tras `expires_in_seconds`."""

    @abstractmethod
    def verify(self, token: str) -> TokenClaims:
        """Valida firma y expiración; lanza InvalidToken si el token no es válido."""
