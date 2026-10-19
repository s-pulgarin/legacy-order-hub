"""Adaptadores falsos en memoria: permiten probar los servicios sin Flask ni base de datos."""

from dataclasses import replace

from orderhub.application.ports.notifier import OrderNotifier
from orderhub.application.ports.repositories import (
    OrderRepository,
    ProductRepository,
    UserRepository,
)
from orderhub.application.ports.unit_of_work import UnitOfWork


class FakeUserRepository(UserRepository):
    def __init__(self, users):
        self._users = {u.username: u for u in users}

    def get_by_username(self, username):
        return self._users.get(username)


class FakeProductRepository(ProductRepository):
    def __init__(self, products):
        self._products = {p.id: p for p in products}

    def get(self, product_id):
        product = self._products.get(product_id)
        return replace(product) if product else None

    def update_stock(self, product):
        self._products[product.id] = replace(product)


class FakeOrderRepository(OrderRepository):
    def __init__(self):
        self._orders = []

    def add(self, order):
        order = replace(order, id=len(self._orders) + 1)
        self._orders.append(order)
        return order

    def list_all(self):
        return list(self._orders)


class FakeUnitOfWork(UnitOfWork):
    def __init__(self, users=(), products=()):
        self.users = FakeUserRepository(users)
        self.products = FakeProductRepository(products)
        self.orders = FakeOrderRepository()
        self.committed = False

    def commit(self):
        self.committed = True

    def rollback(self):
        pass


class FakeNotifier(OrderNotifier):
    def __init__(self):
        self.notified = []

    def order_created(self, order):
        self.notified.append(order)
