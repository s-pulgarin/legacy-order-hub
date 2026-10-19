import pytest

from orderhub.application.services.order_service import OrderService
from orderhub.domain.entities import Product
from orderhub.domain.exceptions import InsufficientStock, InvalidInput, ProductNotFound
from tests.unit.fakes import FakeNotifier, FakeUnitOfWork


@pytest.fixture
def uow():
    return FakeUnitOfWork(products=[Product(1, "Laptop Legada", 1200.0, 5)])


@pytest.fixture
def notifier():
    return FakeNotifier()


@pytest.fixture
def service(uow, notifier):
    return OrderService(lambda: uow, notifier)


def test_create_order_calculates_total_and_decreases_stock(service, uow, notifier):
    order = service.create_order(user_id=2, product_id=1, quantity=2)

    assert order.id == 1
    assert order.total == 2400.0
    assert order.status == "PENDING"
    assert uow.products.get(1).stock == 3
    assert uow.committed
    assert notifier.notified == [order]


def test_create_order_unknown_product_raises(service, uow, notifier):
    with pytest.raises(ProductNotFound):
        service.create_order(user_id=2, product_id=99, quantity=1)
    assert not uow.committed
    assert notifier.notified == []


def test_create_order_insufficient_stock_raises(service, uow):
    with pytest.raises(InsufficientStock):
        service.create_order(user_id=2, product_id=1, quantity=6)
    assert uow.products.get(1).stock == 5
    assert not uow.committed


@pytest.mark.parametrize("quantity", [0, -3])
def test_create_order_non_positive_quantity_raises(service, uow, quantity):
    with pytest.raises(InvalidInput):
        service.create_order(user_id=2, product_id=1, quantity=quantity)
    assert uow.products.get(1).stock == 5


def test_list_orders_returns_created_orders(service):
    service.create_order(user_id=2, product_id=1, quantity=1)
    service.create_order(user_id=2, product_id=1, quantity=1)
    assert [o.id for o in service.list_orders()] == [1, 2]
