"""Pruebas de las entidades de dominio: inventario (RF-02.3), órdenes y roles."""

import pytest

from orderhub.domain.entities import Order, Product, User
from orderhub.domain.exceptions import InsufficientStockException, InvalidInput


def _laptop():
    return Product(1, "Laptop Legada", 1200.0, 5)


def test_decrease_stock_descuenta_las_unidades():
    product = _laptop()
    product.decrease_stock(2)
    assert product.stock == 3


def test_decrease_stock_permite_vender_todo_el_stock():
    product = _laptop()
    product.decrease_stock(5)
    assert product.stock == 0


def test_decrease_stock_mayor_al_stock_lanza_excepcion_sin_modificarlo():
    product = _laptop()
    with pytest.raises(InsufficientStockException):
        product.decrease_stock(6)
    assert product.stock == 5


@pytest.mark.parametrize("quantity", [0, -3])
def test_decrease_stock_con_cantidad_no_positiva_lanza_invalid_input(quantity):
    product = _laptop()
    with pytest.raises(InvalidInput):
        product.decrease_stock(quantity)
    assert product.stock == 5


def test_has_stock_compara_con_el_disponible():
    product = _laptop()
    assert product.has_stock(5)
    assert not product.has_stock(6)


@pytest.mark.parametrize("quantity", [0, -1])
def test_order_place_rechaza_cantidades_no_positivas(quantity):
    with pytest.raises(InvalidInput):
        Order.place(user_id=1, product=_laptop(), quantity=quantity)


def test_order_place_calcula_el_total_y_queda_pendiente():
    order = Order.place(user_id=1, product=_laptop(), quantity=2)
    assert (order.total, order.status, order.id) == (2400.0, "PENDING", None)


@pytest.mark.parametrize("role, expected", [("admin", True), ("client", False)])
def test_user_is_admin_segun_el_rol(role, expected):
    assert User(1, "ana", "hash", role).is_admin is expected
