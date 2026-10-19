"""Pruebas del adaptador Argon2PasswordHasher contra la librería real."""

from orderhub.adapters.outbound.security.argon2_hasher import Argon2PasswordHasher


def test_hash_no_contiene_la_contrasena_y_usa_argon2id():
    hasher = Argon2PasswordHasher()
    password_hash = hasher.hash("admin123")

    assert "admin123" not in password_hash
    assert password_hash.startswith("$argon2id$")
    assert hasher.is_hash(password_hash)


def test_hash_usa_sal_aleatoria():
    hasher = Argon2PasswordHasher()
    assert hasher.hash("admin123") != hasher.hash("admin123")


def test_verify_acepta_la_correcta_y_rechaza_la_incorrecta():
    hasher = Argon2PasswordHasher()
    password_hash = hasher.hash("admin123")

    assert hasher.verify("admin123", password_hash)
    assert not hasher.verify("otra", password_hash)


def test_verify_con_hash_invalido_devuelve_false():
    hasher = Argon2PasswordHasher()

    assert not hasher.verify("admin123", "admin123")
    assert not hasher.is_hash("admin123")
