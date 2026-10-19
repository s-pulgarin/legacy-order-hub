"""Traducción de entidades de dominio a JSON de la API."""

from dataclasses import asdict

from orderhub.domain.entities import Order, User


def user_to_dict(user: User) -> dict:
    data = asdict(user)
    data.pop("password")  # Nunca exponer la contraseña (el legado la devolvía).
    return data


def order_to_dict(order: Order) -> dict:
    return asdict(order)
