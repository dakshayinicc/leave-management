
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
    leave_balance = data.get("leave_balance", 12)

    if not name or not email or not department or not password:
        raise ValueError("All employee fields are required.")

    if "@" not in email:
        raise ValueError("Enter a valid email address.")

    if len(password) < 12:
        raise ValueError("Password must contain at least 12 characters.")

    if get_user_by_email(email):
        raise ValueError("An account with this email already exists.")

    if (isinstance(leave_balance, bool) or
            not isinstance(leave_balance, int) or
            leave_balance < 0 or
            leave_balance > 365):
        raise ValueError("Leave balance must be an integer between 0 and 365.")

    employee = Employee(
        name=name,
        email=email,
        department=department,
        leave_balance=leave_balance,
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
    return get_all_employees()
