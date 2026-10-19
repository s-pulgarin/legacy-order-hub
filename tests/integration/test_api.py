"""Pruebas de extremo a extremo: Flask + servicios + SQLite real en un archivo temporal."""

import sqlite3

import pytest

from orderhub import create_app
from orderhub.container import build_container


@pytest.fixture
def db_path(tmp_path):
    return str(tmp_path / "test_orderhub.db")


@pytest.fixture
def client(db_path):
    app = create_app(container=build_container(db_path), secret_key="test")
    app.config['TESTING'] = True
    return app.test_client()


def _stock(db_path, product_id):
    conn = sqlite3.connect(db_path)
    stock = conn.execute("SELECT stock FROM products WHERE id = ?", (product_id,)).fetchone()[0]
    conn.close()
    return stock


def test_index_renders(client):
    response = client.get('/')
    assert response.status_code == 200
    assert b"Legacy OrderHub" in response.data


def test_login_success_does_not_expose_password(client):
    response = client.post('/login', json={"username": "admin", "password": "admin123"})
    body = response.get_json()
    assert response.status_code == 200
    assert body["status"] == "success"
    assert body["user"] == {"id": 1, "username": "admin", "role": "admin"}


def test_login_wrong_password_returns_401(client):
    response = client.post('/login', json={"username": "admin", "password": "mala"})
    assert response.status_code == 401
    assert response.get_json() == {"status": "error", "message": "Credenciales inválidas"}


def test_login_sql_injection_is_rejected(client):
    payload = {"username": "' OR '1'='1", "password": "' OR '1'='1"}
    response = client.post('/login', json=payload)
    assert response.status_code == 401


def test_create_order_persists_and_decreases_stock(client, db_path):
    response = client.post('/create_order', json={"user_id": 2, "product_id": 2, "quantity": 4})
    assert response.status_code == 201
    assert response.get_json() == {"message": "Orden creada con éxito", "order_id": 1, "total": 62.0}
    assert _stock(db_path, 2) == 46

    orders = client.get('/get_all_orders_legacy').get_json()
    assert orders == [{"id": 1, "user_id": 2, "product_id": 2, "quantity": 4, "total": 62.0, "status": "PENDING"}]


def test_create_order_insufficient_stock_returns_400(client, db_path):
    response = client.post('/create_order', json={"user_id": 2, "product_id": 1, "quantity": 99})
    assert response.status_code == 400
    assert response.get_json() == {"error": "Stock insuficiente"}
    assert _stock(db_path, 1) == 5


def test_create_order_unknown_product_returns_404(client):
    response = client.post('/create_order', json={"user_id": 2, "product_id": 999})
    assert response.status_code == 404
    assert response.get_json() == {"error": "Producto no encontrado"}


@pytest.mark.parametrize("quantity", ["abc", 0, -1])
def test_create_order_invalid_quantity_returns_400(client, quantity):
    response = client.post('/create_order', json={"user_id": 2, "product_id": 1, "quantity": quantity})
    assert response.status_code == 400


def test_seed_passwords_are_stored_hashed(db_path, client):
    conn = sqlite3.connect(db_path)
    passwords = [row[0] for row in conn.execute("SELECT password FROM users")]
    conn.close()
    assert passwords and all(p.startswith("$argon2id$") for p in passwords)


def test_legacy_plaintext_passwords_are_migrated(db_path):
    conn = sqlite3.connect(db_path)
    conn.execute("CREATE TABLE users (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT, password TEXT, role TEXT)")
    conn.execute("INSERT INTO users (username, password, role) VALUES ('admin', 'admin123', 'admin')")
    conn.commit()
    conn.close()

    app = create_app(container=build_container(db_path), secret_key="test")
    response = app.test_client().post('/login', json={"username": "admin", "password": "admin123"})

    assert response.status_code == 200
    conn = sqlite3.connect(db_path)
    stored = conn.execute("SELECT password FROM users WHERE username = 'admin'").fetchone()[0]
    conn.close()
    assert stored.startswith("$argon2id$")


def test_register_then_login(client):
    response = client.post('/register', json={"username": "maria", "password": "secreta123"})
    assert response.status_code == 201
    assert response.get_json()["user"] == {"id": 3, "username": "maria", "role": "client"}

    response = client.post('/login', json={"username": "maria", "password": "secreta123"})
    assert response.status_code == 200


def test_register_duplicate_returns_409(client):
    response = client.post('/register', json={"username": "admin", "password": "otraclave123"})
    assert response.status_code == 409


def test_register_short_password_returns_400(client):
    response = client.post('/register', json={"username": "maria", "password": "corta"})
    assert response.status_code == 400
