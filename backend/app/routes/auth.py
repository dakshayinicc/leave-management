
from flask import Blueprint, request, jsonify
from flask_jwt_extended import (
    create_access_token,
    jwt_required,
    get_jwt_identity
)
from werkzeug.security import check_password_hash

from ..models import User

auth_bp = Blueprint("auth", __name__, url_prefix="/auth")


@auth_bp.route("/login", methods=["POST"])
def login():
    data = request.get_json(silent=True) or {}

    email = data.get("email", "").strip().lower()
    password = data.get("password", "")

    if not email or not password:
        return jsonify({"error": "Email and password required"}), 400

    user = User.query.filter_by(email=email).first()

    if not user or not check_password_hash(
        user.password_hash, password
    ):
        return jsonify({"error": "Invalid email or password"}), 401

    if not user.is_active:
        return jsonify({"error": "Account is inactive"}), 403

    token = create_access_token(identity=str(user.id))

    return jsonify({
        "message": "Login successful",
        "access_token": token,
        "user": {
            "id": user.id,
            "email": user.email,
            "role": user.role
        }
    }), 200


@auth_bp.route("/me", methods=["GET"])
@jwt_required()
def current_user():
    user_id = get_jwt_identity()
    user = User.query.get(int(user_id))

    if not user or not user.is_active:
        return jsonify({"error": "Unauthorized"}), 401

    result = {
        "id": user.id,
        "email": user.email,
        "role": user.role,
    }

    if user.employee:
        result["employee"] = {
            "id": user.employee.id,
            "name": user.employee.name,
            "leave_balance": user.employee.leave_balance,
        }

    return jsonify(result), 200

from functools import wraps
from flask import jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from ..models import User


def role_required(*roles):
    def decorator(func):
        @wraps(func)
        @jwt_required()
        def wrapper(*args, **kwargs):
            user = User.query.get(int(get_jwt_identity()))

            if not user or not user.is_active:
                return jsonify({"error": "Unauthorized"}), 401

            if user.role not in roles:
                return jsonify({"error": "Forbidden"}), 403

            return func(*args, **kwargs)

        return wrapper
    return decorator
