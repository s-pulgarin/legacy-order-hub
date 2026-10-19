"""Traducción de entidades de dominio a JSON de la API."""

from dataclasses import asdict

from orderhub.domain.entities import Order, Product, User


def user_to_dict(user: User) -> dict:
    """Serializa un usuario sin su contraseña (hash)."""
    data = asdict(user)
    data.pop("password")  # Nunca exponer la contraseña (el legado la devolvía).
    return data


def order_to_dict(order: Order) -> dict:
    """Serializa una orden con los mismos campos que la tabla `orders`."""
    return asdict(order)


def product_to_dict(product: Product) -> dict:
    """Serializa un producto del catálogo."""
    return asdict(product)
