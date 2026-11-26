
from app import db
from app.models import LeaveRequest


def save_leave(leave):
    db.session.add(leave)
    db.session.commit()
    return leave


def get_leave_by_id(leave_id):
    return db.session.get(LeaveRequest, leave_id)


def get_all_leaves(status=None):
    query = LeaveRequest.query

    if status:
        query = query.filter_by(status=status.upper())

    return query.order_by(LeaveRequest.id.desc()).all()


def get_approved_overlapping_leave(employee_id, from_date, to_date):
    return LeaveRequest.query.filter(
        LeaveRequest.employee_id == employee_id,
        LeaveRequest.status == "APPROVED",
        LeaveRequest.from_date <= to_date,
        LeaveRequest.to_date >= from_date,
    ).first()
