from flask import Blueprint, current_app, jsonify, request

from orderhub.adapters.inbound.web.serializers import user_to_dict

bp = Blueprint("auth", __name__)


@bp.route('/login', methods=['POST'])
def login():
    data = request.get_json(silent=True) or {}
    auth_service = current_app.extensions["orderhub"].auth_service

    user = auth_service.login(data.get('username'), data.get('password'))
    return jsonify({"status": "success", "user": user_to_dict(user)}), 200
