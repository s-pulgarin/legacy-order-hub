"""Configuración de OrderHub leída de variables de entorno (RNF-02.1).

Los valores se toman de `os.environ`. En desarrollo, `python-dotenv` carga
antes el archivo `.env` (que no se versiona; ver `.env.example`). Una
variable definida en el entorno real tiene prioridad sobre el `.env`.
Ningún secreto vive en el código: si falta `SECRET_KEY`, la app no arranca.
"""

import os
from dataclasses import dataclass, field
from typing import Mapping, Optional, Tuple

from dotenv import load_dotenv

MIN_SECRET_KEY_LENGTH = 32

# Valores que nunca deben usarse como clave: el secreto legado que quedó
# publicado en el historial de Git y el marcador de posición de .env.example.
INSECURE_SECRET_KEYS = {
    "clave_secreta_super_insegura_123",
    "cambia-esto-por-una-clave-aleatoria-de-al-menos-32-caracteres",
}


class ConfigError(RuntimeError):
    """La configuración del entorno falta o no es válida."""


@dataclass(frozen=True)
class Settings:
    """Configuración ya validada que usa el punto de entrada (`app.py`)."""

    secret_key: str
    database_path: str = "orderhub.db"
    jwt_expires_minutes: int = 30
    debug: bool = False
    host: str = "127.0.0.1"
    port: int = 5000
    seed_users: Tuple[Tuple[str, str, str], ...] = field(default_factory=tuple)


def load_settings(
    environ: Optional[Mapping[str, str]] = None, dotenv_path: Optional[str] = None
) -> Settings:
    """Carga `.env` (si existe), lee las variables y devuelve un Settings validado.

    `environ` permite pasar un diccionario en lugar de `os.environ` (pruebas).
    Lanza ConfigError si `SECRET_KEY` falta, es corta o es un valor inseguro
    conocido, o si un número o booleano tiene un formato inválido.
    """
    if environ is None:
        load_dotenv(dotenv_path=dotenv_path, override=False)
        environ = os.environ

    secret_key = _required(environ, "SECRET_KEY")
    if len(secret_key) < MIN_SECRET_KEY_LENGTH:
        raise ConfigError(
            f"SECRET_KEY debe tener al menos {MIN_SECRET_KEY_LENGTH} caracteres"
        )
    if secret_key in INSECURE_SECRET_KEYS:
        raise ConfigError("SECRET_KEY usa un valor publicado; genera una clave nueva")

    return Settings(
        secret_key=secret_key,
        database_path=environ.get("DATABASE_PATH", "").strip() or "orderhub.db",
        jwt_expires_minutes=_int(environ, "JWT_EXPIRES_MINUTES", 30),
        debug=_bool(environ, "FLASK_DEBUG", False),
        host=environ.get("FLASK_HOST", "").strip() or "127.0.0.1",
        port=_int(environ, "FLASK_PORT", 5000),
        seed_users=_seed_users(environ),
    )


def _required(environ: Mapping[str, str], name: str) -> str:
    """Devuelve la variable `name` o lanza ConfigError si falta o está vacía."""
    value = environ.get(name, "").strip()
    if not value:
        raise ConfigError(f"Falta la variable de entorno obligatoria {name}")
    return value


def _int(environ: Mapping[str, str], name: str, default: int) -> int:
    """Lee un entero positivo; usa `default` si la variable no está definida."""
    raw = environ.get(name, "").strip()
    if not raw:
        return default
    try:
        value = int(raw)
    except ValueError:
        raise ConfigError(f"{name} debe ser un número entero")
    if value <= 0:
        raise ConfigError(f"{name} debe ser mayor que cero")
    return value


def _bool(environ: Mapping[str, str], name: str, default: bool) -> bool:
    """Lee un booleano (`true/false`, `1/0`, `yes/no`, `on/off`)."""
    raw = environ.get(name, "").strip().lower()
    if not raw:
        return default
    if raw in {"1", "true", "yes", "on"}:
        return True
    if raw in {"0", "false", "no", "off"}:
        return False
    raise ConfigError(f"{name} debe ser true o false")


def _seed_users(environ: Mapping[str, str]) -> Tuple[Tuple[str, str, str], ...]:
    """Usuarios semilla con contraseña del entorno; sin contraseña no se crean."""
    seeds = []
    for username, role, variable in (
        ("admin", "admin", "SEED_ADMIN_PASSWORD"),
        ("juan", "client", "SEED_CLIENT_PASSWORD"),
    ):
        password = environ.get(variable, "").strip()
        if password:
            seeds.append((username, password, role))
    return tuple(seeds)
