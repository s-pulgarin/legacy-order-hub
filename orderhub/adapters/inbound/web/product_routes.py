"""Rutas HTTP del catálogo de productos: consulta pública y creación (solo admin)."""

from flask import Blueprint, current_app, jsonify, request

from orderhub.adapters.inbound.web.auth_decorators import admin_required
from orderhub.adapters.inbound.web.serializers import product_to_dict
from orderhub.domain.exceptions import InvalidInput

bp = Blueprint("products", __name__)


def _product_service():
    """Obtiene el ProductService inyectado en la aplicación."""
    return current_app.extensions["orderhub"].product_service


@bp.route("/products", methods=["GET"])
def list_products():
    """Lista los productos con su precio y stock actual (RF-02.1). Pública."""
    products = _product_service().list_products()
    return jsonify([product_to_dict(p) for p in products]), 200


@bp.route("/products", methods=["POST"])
@admin_required
def create_product():
    """Crea un producto (solo admin). 201 si se crea; 400 datos inválidos; 401/403 sin
    permisos.
    """
    data = request.get_json(silent=True) or {}
    try:
        price = float(data.get("price"))
        stock = int(data.get("stock", 0))
    except (TypeError, ValueError):
        raise InvalidInput("price debe ser numérico y stock un número entero")

    product = _product_service().create_product(
        name=data.get("name"), price=price, stock=stock
    )
    return jsonify({"status": "success", "product": product_to_dict(product)}), 201
