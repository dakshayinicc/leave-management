
from datetime import date
from decimal import Decimal, InvalidOperation
from app import db
from app.models import Employee, LeaveRequest
from app.repositories.leave_repository import (
    save_leave,
    get_leave_by_id,
    get_all_leaves,
    get_approved_overlapping_leave,
)


LEAVE_TYPES = {
    "CASUAL": "casual_balance",
    "SICK": "sick_balance",
    "COMP_OFF": "comp_off_balance",
    "UNPAID": None,
}


def completed_months(start_date, today=None):
    today = today or date.today()
    months = (today.year - start_date.year) * 12 + today.month - start_date.month
    if today.day < start_date.day:
        months -= 1
    return max(0, months)


def accrue_leave(employee, today=None):
    """Apply missing monthly accruals after six completed probation months."""
    eligible_months = max(0, completed_months(employee.joining_date, today) - 6)
    missing_months = eligible_months - employee.accrued_months
    if missing_months <= 0:
        return

    employee.casual_balance += Decimal(missing_months)
    employee.sick_balance += Decimal("0.5") * missing_months
    employee.accrued_months = eligible_months
    db.session.commit()


def apply_leave(data, employee_id):
    employee = db.session.get(Employee, employee_id)

    if not employee:
        raise LookupError("Employee not found.")

    try:
        from_date = date.fromisoformat(data.get("from_date", ""))
        to_date = date.fromisoformat(data.get("to_date", ""))
    except (ValueError, TypeError):
        raise ValueError("from_date and to_date must use YYYY-MM-DD format.")

    reason = data.get("reason", "").strip()
    leave_type = str(data.get("leave_type", "CASUAL")).upper()

    try:
        duration = Decimal(str(data.get("duration", "1")))
    except (InvalidOperation, TypeError):
        raise ValueError("duration must be a positive number.")

    if leave_type not in LEAVE_TYPES:
        raise ValueError("leave_type must be CASUAL, SICK, COMP_OFF, or UNPAID.")

    if duration <= 0 or duration % Decimal("0.5") != 0:
        raise ValueError("duration must be in half-day increments.")

    if to_date < from_date:
        raise ValueError("to_date must be on or after from_date.")

    if not reason:
        raise ValueError("reason is required.")

    accrue_leave(employee)
    balance_field = LEAVE_TYPES[leave_type]
    date_span = Decimal((to_date - from_date).days + 1)
    if duration > date_span:
        raise ValueError("duration cannot exceed the calendar days in the from_date/to_date range.")
    balance = Decimal("0") if balance_field is None else getattr(employee, balance_field)

    if balance_field is not None and duration > balance:
        raise ValueError(f"Insufficient {balance_field} for the requested duration.")

    if get_approved_overlapping_leave(employee_id, from_date, to_date):
        raise RuntimeError("from_date/to_date overlap with an approved leave_request.")

    leave = LeaveRequest(
        employee_id=employee_id,
        from_date=from_date,
        to_date=to_date,
        reason=reason,
        leave_type=leave_type,
        duration=duration,
        status="PENDING",
    )

    return save_leave(leave)


def list_leaves(status=None):
    allowed = ["PENDING", "APPROVED", "REJECTED"]

    if status and status.upper() not in allowed:
        raise ValueError("Invalid leave status.")

    return get_all_leaves(status)


def process_leave(leave_id, decision):
    leave = get_leave_by_id(leave_id)

    if not leave:
        raise LookupError("Leave request not found.")

    if leave.status != "PENDING":
        raise RuntimeError("Leave request has already been processed.")

    if decision == "APPROVED":
        employee = db.session.get(Employee, leave.employee_id)

        if not employee:
            raise LookupError("Employee not found.")

        balance_field = LEAVE_TYPES[leave.leave_type]

        if balance_field is not None:
            accrue_leave(employee)
            if leave.duration > getattr(employee, balance_field):
                raise ValueError(f"Insufficient {balance_field} for requested duration.")

        if get_approved_overlapping_leave(
            employee.id, leave.from_date, leave.to_date
        ):
            raise RuntimeError("Leave overlaps with an approved request.")

        if balance_field is not None:
            setattr(
                employee,
                balance_field,
                getattr(employee, balance_field) - leave.duration,
            )

    leave.status = decision

    try:
        db.session.commit()
    except Exception:
        db.session.rollback()
        raise

    return leave
