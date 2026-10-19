"""Pruebas de extremo a extremo: Flask + servicios + SQLite real en archivo temporal."""

import sqlite3

import pytest

from orderhub import create_app
from orderhub.container import build_container

SECRET = "clave-de-pruebas-de-al-menos-32-bytes!!"
SEED_USERS = [("admin", "admin123", "admin"), ("juan", "123456", "client")]


@pytest.fixture
def db_path(tmp_path):
    return str(tmp_path / "test_orderhub.db")


@pytest.fixture
def client(db_path):
    app = create_app(
        container=build_container(db_path, SECRET, seed_users=SEED_USERS),
        secret_key=SECRET,
    )
    app.config["TESTING"] = True
    return app.test_client()


def _login(client, username, password):
    response = client.post("/login", json={"username": username, "password": password})
    assert response.status_code == 200
    return {"Authorization": f"Bearer {response.get_json()['token']}"}


@pytest.fixture
def admin_headers(client):
    return _login(client, "admin", "admin123")


@pytest.fixture
def client_headers(client):
    return _login(client, "juan", "123456")


def _stock(db_path, product_id):
    conn = sqlite3.connect(db_path)
    stock = conn.execute(
        "SELECT stock FROM products WHERE id = ?", (product_id,)
    ).fetchone()[0]
    conn.close()
    return stock


def test_index_renders(client):
    response = client.get("/")
    assert response.status_code == 200
    assert b"Legacy OrderHub" in response.data


# --- Login y registro (RF-01.1, RF-01.2) -----------------------------------


def test_login_success_returns_token_and_hides_password(client):
    response = client.post("/login", json={"username": "admin", "password": "admin123"})
    body = response.get_json()
    assert response.status_code == 200
    assert body["status"] == "success"
    assert body["user"] == {"id": 1, "username": "admin", "role": "admin"}
    assert body["token_type"] == "Bearer"
    assert body["expires_in"] == 1800
    assert body["token"].count(".") == 2


def test_login_wrong_password_returns_401(client):
    response = client.post("/login", json={"username": "admin", "password": "mala"})
    assert response.status_code == 401
    assert response.get_json() == {
        "status": "error",
        "message": "Credenciales inválidas",
    }


def test_login_sql_injection_is_rejected(client):
    payload = {"username": "' OR '1'='1", "password": "' OR '1'='1"}
    response = client.post("/login", json=payload)
    assert response.status_code == 401


def test_seed_passwords_are_stored_hashed(db_path, client):
    conn = sqlite3.connect(db_path)
    passwords = [row[0] for row in conn.execute("SELECT password FROM users")]
    conn.close()
    assert passwords and all(p.startswith("$argon2id$") for p in passwords)


def test_legacy_plaintext_passwords_are_migrated(db_path):
    conn = sqlite3.connect(db_path)
    conn.execute(
        "CREATE TABLE users (id INTEGER PRIMARY KEY AUTOINCREMENT,"
        " username TEXT, password TEXT, role TEXT)"
    )
    conn.execute(
        "INSERT INTO users (username, password, role)"
        " VALUES ('admin', 'admin123', 'admin')"
    )
    conn.commit()
    conn.close()

    app = create_app(
        container=build_container(db_path, SECRET, seed_users=SEED_USERS),
        secret_key=SECRET,
    )
    response = app.test_client().post(
        "/login", json={"username": "admin", "password": "admin123"}
    )

    assert response.status_code == 200
    conn = sqlite3.connect(db_path)
    stored = conn.execute(
        "SELECT password FROM users WHERE username = 'admin'"
    ).fetchone()[0]
    conn.close()
    assert stored.startswith("$argon2id$")


def test_register_then_login(client):
    response = client.post(
        "/register", json={"username": "maria", "password": "secreta123"}
    )
    assert response.status_code == 201
    assert response.get_json()["user"] == {
        "id": 3,
        "username": "maria",
        "role": "client",
    }
    _login(client, "maria", "secreta123")


def test_register_duplicate_returns_409(client):
    response = client.post(
        "/register", json={"username": "admin", "password": "otraclave123"}
    )
    assert response.status_code == 409


def test_register_short_password_returns_400(client):
    response = client.post("/register", json={"username": "maria", "password": "x"})
    assert response.status_code == 400


# --- Sesión con JWT (RF-01.3) ----------------------------------------------


@pytest.mark.parametrize(
    "headers",
    [
        {},
        {"Authorization": "Bearer"},
        {"Authorization": "Basic YWRtaW46YWRtaW4xMjM="},
        {"Authorization": "Bearer token.falso.123"},
    ],
)
def test_create_order_without_valid_token_returns_401(client, db_path, headers):
    response = client.post(
        "/create_order", json={"product_id": 1, "quantity": 1}, headers=headers
    )
    assert response.status_code == 401
    assert response.get_json()["status"] == "error"
    assert _stock(db_path, 1) == 5


def test_create_order_uses_user_from_token(client, admin_headers, client_headers):
    response = client.post(
        "/create_order",
        json={"user_id": 1, "product_id": 2, "quantity": 4},
        headers=client_headers,
    )
    assert response.status_code == 201
    assert response.get_json() == {
        "message": "Orden creada con éxito",
        "order_id": 1,
        "total": 62.0,
    }

    orders = client.get("/get_all_orders_legacy", headers=admin_headers).get_json()
    assert orders[0]["user_id"] == 2  # juan, no el user_id=1 enviado en el cuerpo


# --- Órdenes (paridad funcional con el legado) -----------------------------


def test_create_order_persists_and_decreases_stock(client, db_path, client_headers):
    response = client.post(
        "/create_order", json={"product_id": 2, "quantity": 4}, headers=client_headers
    )
    assert response.status_code == 201
    assert _stock(db_path, 2) == 46


def test_create_order_insufficient_stock_returns_400(client, db_path, client_headers):
    response = client.post(
        "/create_order",
        json={"product_id": 1, "quantity": 99},
        headers=client_headers,
    )
    assert response.status_code == 400
    assert response.get_json() == {"error": "Stock insuficiente"}
    assert _stock(db_path, 1) == 5


def test_create_order_unknown_product_returns_404(client, client_headers):
    response = client.post(
        "/create_order", json={"product_id": 999}, headers=client_headers
    )
    assert response.status_code == 404
    assert response.get_json() == {"error": "Producto no encontrado"}


@pytest.mark.parametrize("quantity", ["abc", 0, -1])
def test_create_order_invalid_quantity_returns_400(client, client_headers, quantity):
    response = client.post(
        "/create_order",
        json={"product_id": 1, "quantity": quantity},
        headers=client_headers,
    )
    assert response.status_code == 400


# --- Control de acceso por rol (RF-01.4) ------------------------------------


def test_admin_can_create_product(client, admin_headers):
    response = client.post(
        "/products",
        json={"name": "Teclado", "price": 45.0, "stock": 10},
        headers=admin_headers,
    )
    assert response.status_code == 201
    assert response.get_json()["product"] == {
        "id": 3,
        "name": "Teclado",
        "price": 45.0,
        "stock": 10,
    }


def test_client_cannot_create_product_returns_403(client, db_path, client_headers):
    response = client.post(
        "/products",
        json={"name": "Teclado", "price": 45.0, "stock": 10},
        headers=client_headers,
    )
    assert response.status_code == 403
    assert response.get_json() == {
        "status": "error",
        "message": "Acceso denegado: se requiere rol admin",
    }
    conn = sqlite3.connect(db_path)
    assert conn.execute("SELECT COUNT(*) FROM products").fetchone()[0] == 2
    conn.close()


def test_create_product_without_token_returns_401(client):
    response = client.post("/products", json={"name": "Teclado", "price": 45.0})
    assert response.status_code == 401


@pytest.mark.parametrize(
    "payload",
    [{"name": "Teclado"}, {"name": "", "price": 1}, {"name": "T", "price": "x"}],
)
def test_create_product_invalid_data_returns_400(client, admin_headers, payload):
    response = client.post("/products", json=payload, headers=admin_headers)
    assert response.status_code == 400


def test_list_all_orders_is_admin_only(client, admin_headers, client_headers):
    assert client.get("/get_all_orders_legacy").status_code == 401
    assert (
        client.get("/get_all_orders_legacy", headers=client_headers).status_code == 403
    )
    assert (
        client.get("/get_all_orders_legacy", headers=admin_headers).status_code == 200
    )


def test_role_cannot_be_escalated_by_forging_token(client):
    forged = "eyJhbGciOiJub25lIn0.eyJzdWIiOiIyIiwicm9sZSI6ImFkbWluIn0."
    response = client.post(
        "/products",
        json={"name": "Teclado", "price": 45.0},
        headers={"Authorization": f"Bearer {forged}"},
    )
    assert response.status_code == 401


# --- Catálogo e inventario (RF-02) --------------------------------------------


def test_list_products_is_public_and_shows_current_stock(client, client_headers):
    response = client.get("/products")
    assert response.status_code == 200
    assert response.get_json() == [
        {"id": 1, "name": "Laptop Legada", "price": 1200.0, "stock": 5},
        {"id": 2, "name": "Mouse USB", "price": 15.5, "stock": 50},
    ]

    client.post(
        "/create_order", json={"product_id": 1, "quantity": 2}, headers=client_headers
    )
    assert client.get("/products").get_json()[0]["stock"] == 3


def test_failure_while_saving_order_rolls_back_stock(
    client, db_path, client_headers, monkeypatch
):
    """Si falla el INSERT de la orden después de descontar stock, se hace rollback."""
    from orderhub.adapters.outbound.persistence.sqlite import order_repository

    def failing_add(self, order):
        raise RuntimeError("fallo simulado de la base de datos")

    monkeypatch.setattr(order_repository.SqliteOrderRepository, "add", failing_add)

    response = client.post(
        "/create_order", json={"product_id": 1, "quantity": 2}, headers=client_headers
    )

    assert response.status_code == 500
    assert _stock(db_path, 1) == 5
    conn = sqlite3.connect(db_path)
    assert conn.execute("SELECT COUNT(*) FROM orders").fetchone()[0] == 0
    conn.close()


# --- Inyección SQL en todos los puntos de entrada (RNF-02.2) -------------------


def test_sql_injection_payloads_are_stored_as_plain_data(
    client, db_path, admin_headers
):
    payload = "x'); DROP TABLE users; --"

    register = client.post(
        "/register", json={"username": payload, "password": "secreta123"}
    )
    product = client.post(
        "/products",
        json={"name": payload, "price": 1, "stock": 1},
        headers=admin_headers,
    )

    assert register.status_code == 201
    assert register.get_json()["user"]["username"] == payload
    assert product.status_code == 201
    assert client.get("/products").get_json()[-1]["name"] == payload
    conn = sqlite3.connect(db_path)
    assert conn.execute("SELECT COUNT(*) FROM users").fetchone()[0] == 3
    conn.close()
    _login(client, payload, "secreta123")
