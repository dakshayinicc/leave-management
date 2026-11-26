
from flask import Blueprint, request, jsonify
from app.services.employee_service import create_employee, list_employees
from app.routes.auth import role_required

employees_bp = Blueprint("employees", __name__, url_prefix="/employees")


@employees_bp.route("", methods=["POST"])
@role_required("ADMIN")
def add_employee():
    try:
        data = request.get_json(silent=True) or {}
        employee = create_employee(data)

        return jsonify({
            "message": "Employee created successfully",
            "employee": {
                "id": employee.id,
                "name": employee.name,
                "email": employee.email,
                "department": employee.department,
                "leave_balance": employee.leave_balance,
            }
        }), 201

    except ValueError as error:
        return jsonify({"error": str(error)}), 400


@employees_bp.route("", methods=["GET"])
@role_required("ADMIN", "MANAGER")
def get_employees():
    employees = list_employees()

    return jsonify([
        {
            "id": employee.id,
            "name": employee.name,
            "email": employee.email,
            "department": employee.department,
            "leave_balance": employee.leave_balance,
        }
        for employee in employees
    ]), 200
