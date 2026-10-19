from flask import Blueprint, current_app, jsonify, request

from orderhub.adapters.inbound.web.serializers import order_to_dict
from orderhub.domain.exceptions import InvalidInput

bp = Blueprint("orders", __name__)


def _order_service():
    return current_app.extensions["orderhub"].order_service


@bp.route('/create_order', methods=['POST'])
def create_order():
    data = request.get_json(silent=True) or {}
    try:
        quantity = int(data.get('quantity', 1))
    except (TypeError, ValueError):
        raise InvalidInput("La cantidad debe ser un número entero")

    order = _order_service().create_order(
        user_id=data.get('user_id'),
        product_id=data.get('product_id'),
        quantity=quantity,
    )
    return jsonify({
        "message": "Orden creada con éxito",
        "order_id": order.id,
        "total": order.total
    }), 201


@bp.route('/get_all_orders_legacy', methods=['GET'])
def get_orders():
    orders = _order_service().list_orders()
    return jsonify([order_to_dict(o) for o in orders]), 200
