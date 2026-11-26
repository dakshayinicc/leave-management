
from datetime import datetime
from decimal import Decimal
from . import db


class Employee(db.Model):
    __tablename__ = "employee"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    department = db.Column(db.String(100), nullable=False)
    # Leave is tracked by type. Decimal values support half-day sick leave.
    casual_balance = db.Column(db.Numeric(6, 1), nullable=False, default=Decimal("0.0"))
    sick_balance = db.Column(db.Numeric(6, 1), nullable=False, default=Decimal("0.0"))
    comp_off_balance = db.Column(db.Numeric(6, 1), nullable=False, default=Decimal("0.0"))
    joining_date = db.Column(db.Date, nullable=False)
    accrued_months = db.Column(db.Integer, nullable=False, default=0)

    leave_requests = db.relationship(
        "LeaveRequest",
        back_populates="employee",
        cascade="all, delete-orphan"
    )

    user = db.relationship(
        "User",
        back_populates="employee",
        uselist=False
    )


class LeaveRequest(db.Model):
    __tablename__ = "leave_request"

    id = db.Column(db.Integer, primary_key=True)

    employee_id = db.Column(
        db.Integer,
        db.ForeignKey("employee.id"),
        nullable=False
    )

    from_date = db.Column(db.Date, nullable=False)
    to_date = db.Column(db.Date, nullable=False)
    reason = db.Column(db.String(500), nullable=False)

    leave_type = db.Column(
        db.String(20),
        nullable=False,
        default="CASUAL"
    )

    duration = db.Column(db.Numeric(4, 1), nullable=False, default=Decimal("1.0"))

    status = db.Column(
        db.String(20),
        nullable=False,
        default="PENDING"
    )

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        nullable=False
    )

    employee = db.relationship(
        "Employee",
        back_populates="leave_requests"
    )

    __table_args__ = (
        db.CheckConstraint(
            "status IN ('PENDING', 'APPROVED', 'REJECTED')",
            name="check_leave_status"
        ),
        db.CheckConstraint(
            "leave_type IN ('CASUAL', 'SICK', 'COMP_OFF')",
            name="check_leave_type"
        ),
        db.CheckConstraint(
            "duration > 0",
            name="check_leave_duration"
        ),
        db.CheckConstraint(
            "to_date >= from_date",
            name="check_leave_dates"
        ),
    )


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)

    email = db.Column(
        db.String(150),
        unique=True,
        nullable=False
    )

    password_hash = db.Column(
        db.String(255),
        nullable=False
    )

    role = db.Column(
        db.String(20),
        nullable=False
    )

    employee_id = db.Column(
        db.Integer,
        db.ForeignKey("employee.id"),
        unique=True,
        nullable=True
    )

    is_active = db.Column(
        db.Boolean,
        nullable=False,
        default=True
    )

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        nullable=False
    )

    employee = db.relationship(
        "Employee",
        back_populates="user"
    )

    __table_args__ = (
        db.CheckConstraint(
            "role IN ('EMPLOYEE', 'MANAGER', 'ADMIN')",
            name="check_user_role"
        ),
    )
