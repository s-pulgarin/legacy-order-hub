"""Pruebas de las reglas de inventario de la entidad Product (RF-02.3)."""

import pytest

from orderhub.domain.entities import Product
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
