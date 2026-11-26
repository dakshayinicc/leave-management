
from getpass import getpass
from werkzeug.security import generate_password_hash

from app import create_app, db
from app.models import Employee, LeaveRequest, User

app = create_app()

with app.app_context():
    # Create all database tables
    db.create_all()
    print("Database tables created successfully!")

    # Create initial admin account
    email = input("Enter admin email: ").strip().lower()

    if User.query.filter_by(email=email).first():
        print("Admin account already exists!")
    else:
        password = getpass("Enter admin password: ")

        if len(password) < 12:
            print("Password must contain at least 12 characters.")
        else:
            admin = User(
                email=email,
                password_hash=generate_password_hash(password),
                role="ADMIN",
                is_active=True
            )

            db.session.add(admin)
            db.session.commit()

            print("Admin account created successfully!")
