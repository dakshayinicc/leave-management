
from datetime import date
from app import db
from app.models import Employee, LeaveRequest
from app.repositories.leave_repository import (
    save_leave,
    get_leave_by_id,
    get_all_leaves,
    get_approved_overlapping_leave,
)


def apply_leave(data, employee_id):
    employee = db.session.get(Employee, employee_id)

    if not employee:
        raise LookupError("Employee not found.")

    try:
        from_date = date.fromisoformat(data.get("from_date", ""))
        to_date = date.fromisoformat(data.get("to_date", ""))
    except (ValueError, TypeError):
        raise ValueError("Dates must use YYYY-MM-DD format.")

    reason = data.get("reason", "").strip()

    if to_date < from_date:
        raise ValueError("End date cannot be before start date.")

    if not reason:
        raise ValueError("Leave reason is required.")

    days = (to_date - from_date).days + 1

    if days > employee.leave_balance:
        raise ValueError("Insufficient leave balance.")

    if get_approved_overlapping_leave(employee_id, from_date, to_date):
        raise ValueError("Leave overlaps with an approved request.")

    leave = LeaveRequest(
        employee_id=employee_id,
        from_date=from_date,
        to_date=to_date,
        reason=reason,
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

        days = (leave.to_date - leave.from_date).days + 1

        if days > employee.leave_balance:
            raise ValueError("Insufficient leave balance.")

        if get_approved_overlapping_leave(
            employee.id, leave.from_date, leave.to_date
        ):
            raise RuntimeError("Leave overlaps with an approved request.")

        employee.leave_balance -= days

    leave.status = decision

    try:
        db.session.commit()
    except Exception:
        db.session.rollback()
        raise

    return leave
