
from app import db
from app.models import Employee, User


def get_all_employees():
    return Employee.query.order_by(Employee.id).all()


def get_employee_by_id(employee_id):
    return db.session.get(Employee, employee_id)


def get_user_by_email(email):
    return User.query.filter_by(email=email).first()


def save_employee(employee, user):
    try:
        db.session.add(employee)
        db.session.add(user)
        db.session.commit()
        return employee
    except Exception:
        db.session.rollback()
        raise
