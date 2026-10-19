"""Pruebas de la carga de configuración desde el entorno (RNF-02.1)."""

from pathlib import Path

import pytest

import config
from config import ConfigError, load_settings

VALID_KEY = "k" * 40


def test_carga_valores_del_entorno():
    settings = load_settings(
        {
            "SECRET_KEY": VALID_KEY,
            "DATABASE_PATH": "otra.db",
            "JWT_EXPIRES_MINUTES": "15",
            "FLASK_DEBUG": "true",
            "FLASK_HOST": "0.0.0.0",
            "FLASK_PORT": "8080",
            "SEED_ADMIN_PASSWORD": "clave-admin",
            "SEED_CLIENT_PASSWORD": "clave-juan",
        }
    )

    assert settings.secret_key == VALID_KEY
    assert settings.database_path == "otra.db"
    assert settings.jwt_expires_minutes == 15
    assert settings.debug is True
    assert (settings.host, settings.port) == ("0.0.0.0", 8080)
    assert settings.seed_users == (
        ("admin", "clave-admin", "admin"),
        ("juan", "clave-juan", "client"),
    )


def test_valores_por_defecto_seguros():
    settings = load_settings({"SECRET_KEY": VALID_KEY})

    assert settings.database_path == "orderhub.db"
    assert settings.jwt_expires_minutes == 30
    assert settings.debug is False
    assert settings.host == "127.0.0.1"
    assert settings.seed_users == ()


@pytest.mark.parametrize(
    "secret",
    [
        "",
        "corta",
        "clave_secreta_super_insegura_123",
        "cambia-esto-por-una-clave-aleatoria-de-al-menos-32-caracteres",
    ],
)
def test_secret_key_ausente_corta_o_publicada_impide_arrancar(secret):
    with pytest.raises(ConfigError):
        load_settings({"SECRET_KEY": secret})


@pytest.mark.parametrize(
    "variable, value",
    [("JWT_EXPIRES_MINUTES", "abc"), ("FLASK_PORT", "-1"), ("FLASK_DEBUG", "quizas")],
)
def test_formatos_invalidos_lanzan_config_error(variable, value):
    with pytest.raises(ConfigError):
        load_settings({"SECRET_KEY": VALID_KEY, variable: value})


def test_lee_el_archivo_env(tmp_path, monkeypatch):
    monkeypatch.delenv("SECRET_KEY", raising=False)
    monkeypatch.delenv("JWT_EXPIRES_MINUTES", raising=False)
    env_file = tmp_path / ".env"
    env_file.write_text(f"SECRET_KEY={VALID_KEY}\nJWT_EXPIRES_MINUTES=5\n")

    settings = load_settings(dotenv_path=str(env_file))

    assert settings.secret_key == VALID_KEY
    assert settings.jwt_expires_minutes == 5


def test_config_no_contiene_secretos_escritos():
    source = Path(config.__file__).read_text(encoding="utf-8")

    assert "admin1234_super_secret" not in source
    assert "DB_PASS" not in source
