
import os
from pathlib import Path

from dotenv import load_dotenv
from flask import Flask, jsonify, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager
from sqlalchemy import URL

BASE_DIR = Path(__file__).resolve().parents[2]
load_dotenv(BASE_DIR / ".env")

db = SQLAlchemy()
jwt = JWTManager()

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
