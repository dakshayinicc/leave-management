
from flask import Blueprint, request, jsonify
from app.services.employee_service import create_employee, list_employees, grant_comp_off
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
                "casual_balance": float(employee.casual_balance),
                "sick_balance": float(employee.sick_balance),
                "comp_off_balance": float(employee.comp_off_balance),
                "joining_date": employee.joining_date.isoformat(),
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
            "casual_balance": float(employee.casual_balance),
            "sick_balance": float(employee.sick_balance),
            "comp_off_balance": float(employee.comp_off_balance),
            "joining_date": employee.joining_date.isoformat(),
        }
        for employee in employees
    ]), 200


@employees_bp.route("/<int:employee_id>/comp-off", methods=["POST"])
@role_required("ADMIN", "MANAGER")
def add_comp_off(employee_id):
    data = request.get_json(silent=True) or {}
    employee = grant_comp_off(employee_id, data.get("amount"))
    return jsonify({
        "message": "Comp-off leave added successfully",
        "employee_id": employee.id,
        "comp_off_balance": float(employee.comp_off_balance),
    }), 200
