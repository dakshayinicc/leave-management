
from datetime import date

from werkzeug.security import generate_password_hash
from app.models import Employee, User
from app.repositories.employee_repository import (
    get_all_employees,
    get_user_by_email,
    save_employee,
)


def create_employee(data):
    name = data.get("name", "").strip()
    email = data.get("email", "").strip().lower()
    department = data.get("department", "").strip()
    password = data.get("password", "")
    joining_date_text = data.get("joining_date", "")

    if not name or not email or not department or not password:
        raise ValueError("All employee fields are required.")

    if "@" not in email:
        raise ValueError("Enter a valid email address.")

    if len(password) < 12:
        raise ValueError("Password must contain at least 12 characters.")

    if get_user_by_email(email):
        raise ValueError("An account with this email already exists.")

    try:
        joining_date = date.fromisoformat(joining_date_text)
    except (ValueError, TypeError):
        raise ValueError("Joining date must use YYYY-MM-DD format.")

    if joining_date > date.today():
        raise ValueError("Joining date cannot be in the future.")

    employee = Employee(
        name=name,
        email=email,
        department=department,
        joining_date=joining_date,
    )

    user = User(
        email=email,
        password_hash=generate_password_hash(password),
        role="EMPLOYEE",
        is_active=True,
        employee=employee,
    )

    save_employee(employee, user)
    return employee


def list_employees():
    from app.services.leave_service import accrue_leave

    employees = get_all_employees()
    for employee in employees:
        accrue_leave(employee)
    return employees


def grant_comp_off(employee_id, amount):
    from decimal import Decimal, InvalidOperation
    from app import db

    employee = db.session.get(Employee, employee_id)
    if not employee:
        raise LookupError("Employee not found.")

    try:
        amount = Decimal(str(amount))
    except (InvalidOperation, TypeError):
        raise ValueError("Comp-off amount must be a positive number.")

    if amount <= 0 or amount % Decimal("0.5") != 0:
        raise ValueError("Comp-off amount must use half-day increments.")

    employee.comp_off_balance += amount
    db.session.commit()
    return employee
