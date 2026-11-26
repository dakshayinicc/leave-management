
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
        "employee_name": leave.employee.name,
        "from_date": leave.from_date.isoformat(),
        "to_date": leave.to_date.isoformat(),
        "reason": leave.reason,
        "leave_type": leave.leave_type,
        "duration": float(leave.duration),
        "status": leave.status,
        "created_at": leave.created_at.isoformat() if leave.created_at else None,
    }


@leaves_bp.route("", methods=["POST"])
@role_required("EMPLOYEE", "MANAGER")
def create_leave():
    try:
        user = db.session.get(User, int(get_jwt_identity()))
        data = request.get_json(silent=True) or {}

        employee_id = user.employee_id
        if employee_id is None:
            raise ValueError("The signed-in user must have an employee profile to apply for leave.")

        leave = apply_leave(data, employee_id)

        return jsonify({
            "message": "Leave request submitted successfully",
            "leave": leave_response(leave),
        }), 201

    except ValueError as error:
        return jsonify({"error": str(error)}), 400
    except RuntimeError as error:
        return jsonify({"error": str(error)}), 409
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
        elif user.role == "MANAGER":
            if request.args.get("mine") == "true":
                leaves = [leave for leave in leaves if leave.employee_id == user.employee_id]
            else:
                department = user.employee.department if user.employee else None
                leaves = [leave for leave in leaves
                          if department and leave.employee.department == department]

        return jsonify([leave_response(leave) for leave in leaves]), 200

    except ValueError as error:
        return jsonify({"error": str(error)}), 400


@leaves_bp.route("/<int:leave_id>/approve", methods=["PUT"])
@role_required("MANAGER", "ADMIN")
def approve_leave(leave_id):
    try:
        user = db.session.get(User, int(get_jwt_identity()))
        from app.repositories.leave_repository import get_leave_by_id
        request_record = get_leave_by_id(leave_id)
        if user.role == "MANAGER" and request_record:
            if request_record.employee_id == user.employee_id:
                return jsonify({"error": "Managers cannot approve their own leave_request."}), 403
            if not user.employee or request_record.employee.department != user.employee.department:
                return jsonify({"error": "This leave_request is outside your department."}), 403
        leave = process_leave(leave_id, "APPROVED")
        return jsonify({
            "message": "Leave approved successfully",
            "leave": leave_response(leave),
        }), 200

    except LookupError as error:
        return jsonify({"error": str(error)}), 404
    except ValueError as error:
        return jsonify({"error": str(error)}), 400
    except RuntimeError as error:
        return jsonify({"error": str(error)}), 409


@leaves_bp.route("/<int:leave_id>/reject", methods=["PUT"])
@role_required("MANAGER", "ADMIN")
def reject_leave(leave_id):
    try:
        user = db.session.get(User, int(get_jwt_identity()))
        from app.repositories.leave_repository import get_leave_by_id
        request_record = get_leave_by_id(leave_id)
        if user.role == "MANAGER" and request_record:
            if request_record.employee_id == user.employee_id:
                return jsonify({"error": "Managers cannot reject their own leave_request."}), 403
            if not user.employee or request_record.employee.department != user.employee.department:
                return jsonify({"error": "This leave_request is outside your department."}), 403
        leave = process_leave(leave_id, "REJECTED")
        return jsonify({
            "message": "Leave rejected successfully",
            "leave": leave_response(leave),
        }), 200

    except LookupError as error:
        return jsonify({"error": str(error)}), 404
    except (ValueError, RuntimeError) as error:
        return jsonify({"error": str(error)}), 409
