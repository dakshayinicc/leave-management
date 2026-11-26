
from flask import Blueprint, request, jsonify
from flask_jwt_extended import get_jwt_identity
from app import db
from app.models import User
from app.services.leave_service import (
    apply_leave,
    list_leaves,
    process_leave,
)
from app.routes.auth import role_required

leaves_bp = Blueprint("leaves", __name__, url_prefix="/leaves")


def leave_response(leave):
    return {
        "id": leave.id,
        "employee_id": leave.employee_id,
        "from_date": leave.from_date.isoformat(),
        "to_date": leave.to_date.isoformat(),
        "reason": leave.reason,
        "status": leave.status,
    }


@leaves_bp.route("", methods=["POST"])
@role_required("EMPLOYEE", "MANAGER", "ADMIN")
def create_leave():
    try:
        user = db.session.get(User, int(get_jwt_identity()))
        data = request.get_json(silent=True) or {}

        employee_id = user.employee_id
        if user.role in ("ADMIN", "MANAGER"):
            employee_id = data.get("employee_id")
            if not isinstance(employee_id, int):
                raise ValueError("employee_id is required for this user role.")

        leave = apply_leave(data, employee_id)

        return jsonify({
            "message": "Leave request submitted successfully",
            "leave": leave_response(leave),
        }), 201

    except ValueError as error:
        return jsonify({"error": str(error)}), 400
    except LookupError as error:
        return jsonify({"error": str(error)}), 404


@leaves_bp.route("", methods=["GET"])
@role_required("EMPLOYEE", "MANAGER", "ADMIN")
def get_leaves():
    try:
        user = db.session.get(User, int(get_jwt_identity()))
        status = request.args.get("status")

        leaves = list_leaves(status)

        if user.role == "EMPLOYEE":
            leaves = [leave for leave in leaves
                      if leave.employee_id == user.employee_id]

        return jsonify([leave_response(leave) for leave in leaves]), 200

    except ValueError as error:
        return jsonify({"error": str(error)}), 400


@leaves_bp.route("/<int:leave_id>/approve", methods=["PUT"])
@role_required("MANAGER", "ADMIN")
def approve_leave(leave_id):
    try:
        leave = process_leave(leave_id, "APPROVED")
        return jsonify({
            "message": "Leave approved successfully",
            "leave": leave_response(leave),
        }), 200

    except LookupError as error:
        return jsonify({"error": str(error)}), 404
    except (ValueError, RuntimeError) as error:
        return jsonify({"error": str(error)}), 409


@leaves_bp.route("/<int:leave_id>/reject", methods=["PUT"])
@role_required("MANAGER", "ADMIN")
def reject_leave(leave_id):
    try:
        leave = process_leave(leave_id, "REJECTED")
        return jsonify({
            "message": "Leave rejected successfully",
            "leave": leave_response(leave),
        }), 200

    except LookupError as error:
        return jsonify({"error": str(error)}), 404
    except (ValueError, RuntimeError) as error:
        return jsonify({"error": str(error)}), 409
