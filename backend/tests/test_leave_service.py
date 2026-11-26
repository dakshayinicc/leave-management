import sys
from datetime import date
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app import db
from app.models import Employee
from app.services.leave_service import apply_leave, process_leave


@pytest.fixture
def app_context():
    from flask import Flask

    test_app = Flask(__name__)
    test_app.config.update(
        TESTING=True,
        SQLALCHEMY_DATABASE_URI="sqlite:///:memory:",
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
    )
    db.init_app(test_app)
    with test_app.app_context():
        db.create_all()
        yield test_app
        db.session.remove()
        db.drop_all()


def make_employee(balance=5):
    employee = Employee(
        name="Test Employee",
        email=f"employee-{balance}@example.com",
        department="IT",
        joining_date=date.today(),
        casual_balance=balance,
    )
    db.session.add(employee)
    db.session.commit()
    return employee


def test_rejects_invalid_dates(app_context):
    employee = make_employee()

    with pytest.raises(ValueError, match="before start"):
        apply_leave({
            "from_date": "2026-06-20",
            "to_date": "2026-06-18",
            "reason": "Personal work",
        }, employee.id)


def test_rejects_insufficient_balance(app_context):
    employee = make_employee(balance=2)

    with pytest.raises(ValueError, match="Insufficient"):
        apply_leave({
            "from_date": "2026-06-18",
            "to_date": "2026-06-20",
            "duration": 3,
            "reason": "Personal work",
        }, employee.id)


def test_rejects_overlap_with_approved_leave(app_context):
    employee = make_employee(balance=10)
    leave = apply_leave({
        "from_date": "2026-06-18",
        "to_date": "2026-06-20",
        "reason": "First trip",
    }, employee.id)
    process_leave(leave.id, "APPROVED")

    with pytest.raises(ValueError, match="overlaps"):
        apply_leave({
            "from_date": "2026-06-19",
            "to_date": "2026-06-21",
            "reason": "Second trip",
        }, employee.id)
