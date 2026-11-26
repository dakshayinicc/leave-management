
import os
from pathlib import Path

from dotenv import load_dotenv
from flask import Flask, jsonify, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager
from sqlalchemy import URL, inspect, text

BASE_DIR = Path(__file__).resolve().parents[2]
load_dotenv(BASE_DIR / ".env")

db = SQLAlchemy()
jwt = JWTManager()


def ensure_leave_schema():
    """Add the typed-leave columns when upgrading an older database."""
    inspector = inspect(db.engine)
    employee_columns = {column["name"] for column in inspector.get_columns("employee")}
    leave_columns = {column["name"] for column in inspector.get_columns("leave_request")}

    with db.engine.begin() as connection:
        additions = {
            "casual_balance": "DECIMAL(6,1) NOT NULL DEFAULT 0.0",
            "sick_balance": "DECIMAL(6,1) NOT NULL DEFAULT 0.0",
            "comp_off_balance": "DECIMAL(6,1) NOT NULL DEFAULT 0.0",
            "joining_date": "DATE NULL",
            "accrued_months": "INT NOT NULL DEFAULT 0",
        }
        for name, definition in additions.items():
            if name not in employee_columns:
                connection.execute(text(f"ALTER TABLE employee ADD COLUMN {name} {definition}"))

        connection.execute(text(
            "UPDATE employee SET joining_date = COALESCE(joining_date, CURRENT_DATE)"
        ))
        if "leave_balance" in employee_columns:
            connection.execute(text(
                "UPDATE employee SET casual_balance = "
                "CASE WHEN casual_balance = 0 THEN COALESCE(leave_balance, 0) "
                "ELSE casual_balance END"
            ))
            # Existing databases keep the legacy NOT NULL column after the
            # typed-balance migration. Give it a default so inserts from the
            # new ORM model (which no longer writes leave_balance) succeed.
            connection.execute(text(
                "ALTER TABLE employee ALTER COLUMN leave_balance SET DEFAULT 0"
            ))

        leave_additions = {
            "leave_type": "VARCHAR(20) NOT NULL DEFAULT 'CASUAL'",
            "duration": "DECIMAL(4,1) NOT NULL DEFAULT 1.0",
        }
        for name, definition in leave_additions.items():
            if name not in leave_columns:
                connection.execute(text(f"ALTER TABLE leave_request ADD COLUMN {name} {definition}"))

def create_app():
    app = Flask(__name__)

    required = [
        "SECRET_KEY",
        "JWT_SECRET_KEY",
        "DB_USER",
        "DB_PASSWORD",
        "DB_HOST",
        "DB_PORT",
        "DB_NAME"
    ]

    missing = [key for key in required if not os.getenv(key)]
    if missing:
        raise RuntimeError(f"Missing environment variables: {missing}")

    app.config["SECRET_KEY"] = os.getenv("SECRET_KEY")
    app.config["JWT_SECRET_KEY"] = os.getenv("JWT_SECRET_KEY")
    app.config["JWT_ACCESS_TOKEN_EXPIRES"] = 3600

    app.config["SQLALCHEMY_DATABASE_URI"] = URL.create(
        "mysql+pymysql",
        username=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        host=os.getenv("DB_HOST"),
        port=int(os.getenv("DB_PORT")),
        database=os.getenv("DB_NAME")
    )

    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    db.init_app(app)
    jwt.init_app(app)

    # Load models before creating database tables
    from app import models
    from app.errors import register_error_handlers
    register_error_handlers(app)

    with app.app_context():
        db.create_all()
        ensure_leave_schema()

    # Register authentication routes
    from app.routes.auth import auth_bp
    app.register_blueprint(auth_bp)

    # Register employee routes after the Flask app has been created
    from app.routes.employees import employees_bp
    app.register_blueprint(employees_bp)

    # Register leave routes after the Flask app has been created
    from app.routes.leaves import leaves_bp
    app.register_blueprint(leaves_bp)

    @app.get("/health")
    def health():
        return jsonify({
            "status": "success",
            "message": "Leave Management API is running"
        }), 200

    frontend_dir = BASE_DIR / "frontend"

    @app.get("/")
    def home():
        return send_from_directory(frontend_dir, "index.html")

    @app.get("/style.css")
    def frontend_css():
        return send_from_directory(frontend_dir, "style.css")

    @app.get("/app.js")
    def frontend_js():
        return send_from_directory(frontend_dir, "app.js")

    return app
