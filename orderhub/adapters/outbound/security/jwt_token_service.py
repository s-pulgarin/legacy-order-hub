"""Adaptador de TokenService basado en JSON Web Tokens (librería PyJWT)."""

from datetime import datetime, timedelta, timezone
from typing import Callable

import jwt

from orderhub.application.ports.token_service import TokenClaims, TokenService
from orderhub.domain.entities import User
from orderhub.domain.exceptions import InvalidToken


def _utcnow() -> datetime:
    """Hora actual en UTC (inyectable para simular el paso del tiempo en tests)."""
    return datetime.now(timezone.utc)


class JWTTokenService(TokenService):
    """Emite JWT firmados con HMAC-SHA256 que incluyen `sub`, `username`, `role`, `iat`
    y `exp`.
    """

    ALGORITHM = "HS256"

    def __init__(
        self,
        secret_key: str,
        expires_minutes: int = 30,
        clock: Callable[[], datetime] = _utcnow,
    ):
        """`secret_key` firma los tokens; `expires_minutes` define su vigencia."""
        if not secret_key:
            raise ValueError("JWTTokenService necesita una clave secreta")
        self._secret_key = secret_key
        self._clock = clock
        self.expires_in_seconds = expires_minutes * 60

    def issue(self, user: User) -> str:
        """Firma un token para `user` con fecha de emisión y de expiración."""
        now = self._clock()
        payload = {
            "sub": str(user.id),
            "username": user.username,
            "role": user.role,
            "iat": now,
            "exp": now + timedelta(seconds=self.expires_in_seconds),
        }
        return jwt.encode(payload, self._secret_key, algorithm=self.ALGORITHM)

    def verify(self, token: str) -> TokenClaims:
        """Decodifica el token exigiendo firma válida, `exp` vigente y los campos de
        identidad.
        """
        try:
            payload = jwt.decode(
                token,
                self._secret_key,
                algorithms=[self.ALGORITHM],
                options={"require": ["exp", "iat", "sub"]},
            )
            return TokenClaims(
                user_id=int(payload["sub"]),
                username=payload["username"],
                role=payload["role"],
            )
        except jwt.ExpiredSignatureError:
            raise InvalidToken("El token ha expirado")
        except (jwt.InvalidTokenError, KeyError, ValueError):
            raise InvalidToken("Token inválido")
