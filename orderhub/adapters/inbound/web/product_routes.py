"""Rutas HTTP administrativas del catálogo de productos."""

from flask import Blueprint, current_app, jsonify, request

from orderhub.adapters.inbound.web.auth_decorators import admin_required
from orderhub.adapters.inbound.web.serializers import product_to_dict
from orderhub.domain.exceptions import InvalidInput

bp = Blueprint("products", __name__)


@bp.route("/products", methods=["POST"])
@admin_required
def create_product():
    """Crea un producto (solo admin). 201 si se crea; 400 datos inválidos; 401/403 sin permisos."""
    data = request.get_json(silent=True) or {}
    try:
        price = float(data.get("price"))
        stock = int(data.get("stock", 0))
    except (TypeError, ValueError):
        raise InvalidInput("price debe ser numérico y stock un número entero")

    product = current_app.extensions["orderhub"].product_service.create_product(
        name=data.get("name"), price=price, stock=stock
    )
    return jsonify({"status": "success", "product": product_to_dict(product)}), 201
