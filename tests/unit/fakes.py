"""Adaptadores falsos en memoria: permiten probar los servicios sin Flask ni base de datos."""

from dataclasses import replace

from orderhub.application.ports.notifier import OrderNotifier
from orderhub.application.ports.password_hasher import PasswordHasher
from orderhub.application.ports.token_service import TokenClaims, TokenService
from orderhub.application.ports.repositories import (
    OrderRepository,
    ProductRepository,
    UserRepository,
)
from orderhub.application.ports.unit_of_work import UnitOfWork
from orderhub.domain.exceptions import InvalidToken


class FakeUserRepository(UserRepository):
    def __init__(self, users):
        self._users = {u.username: u for u in users}

    def get_by_username(self, username):
        return self._users.get(username)

    def add(self, user):
        user = replace(user, id=len(self._users) + 1)
        self._users[user.username] = user
        return user


class FakeProductRepository(ProductRepository):
    def __init__(self, products):
        self._products = {p.id: p for p in products}

    def get(self, product_id):
        product = self._products.get(product_id)
        return replace(product) if product else None

    def add(self, product):
        product = replace(product, id=len(self._products) + 1)
        self._products[product.id] = product
        return product

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


class FakePasswordHasher(PasswordHasher):
    """Hash reversible y legible, solo para pruebas: "hashed:<contraseña>"."""

    PREFIX = "hashed:"

    def hash(self, plain_password):
        return self.PREFIX + plain_password

    def verify(self, plain_password, password_hash):
        return password_hash == self.PREFIX + plain_password

    def is_hash(self, value):
        return value.startswith(self.PREFIX)


class FakeTokenService(TokenService):
    """Token legible "token:<id>:<username>:<role>", solo para pruebas."""

    expires_in_seconds = 1800

    def issue(self, user):
        return f"token:{user.id}:{user.username}:{user.role}"

    def verify(self, token):
        try:
            prefix, user_id, username, role = token.split(":")
            assert prefix == "token"
            return TokenClaims(int(user_id), username, role)
        except (ValueError, AssertionError):
            raise InvalidToken()
