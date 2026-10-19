"""Pruebas unitarias de ProductService con una Unit of Work falsa."""

import pytest

from orderhub.application.services.product_service import ProductService
from orderhub.domain.exceptions import InvalidInput
from tests.unit.fakes import FakeUnitOfWork


@pytest.fixture
def uow():
    return FakeUnitOfWork()


@pytest.fixture
def service(uow):
    return ProductService(lambda: uow)


def test_create_product_lo_persiste_con_id(service, uow):
    product = service.create_product("  Teclado  ", 45.0, 10)

    assert product.id == 1
    assert product.name == "Teclado"
    assert uow.products.get(1) == product
    assert uow.committed


@pytest.mark.parametrize(
    "name, price, stock",
    [
        ("", 10.0, 1),
        ("Teclado", 0, 1),
        ("Teclado", float("nan"), 1),
        ("Teclado", 10.0, -1),
    ],
)
def test_create_product_con_datos_invalidos_lanza_invalid_input(
    service, uow, name, price, stock
):
    with pytest.raises(InvalidInput):
        service.create_product(name, price, stock)
    assert not uow.committed


def test_list_products_devuelve_catalogo_con_stock(service):
    service.create_product("Teclado", 45.0, 10)
    service.create_product("Monitor", 300.0, 2)

    products = service.list_products()

    assert [(p.name, p.stock) for p in products] == [("Teclado", 10), ("Monitor", 2)]
