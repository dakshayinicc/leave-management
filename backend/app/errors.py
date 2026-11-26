from flask import jsonify
from werkzeug.exceptions import HTTPException
from sqlalchemy.exc import IntegrityError


def register_error_handlers(app):
    """Register consistent JSON responses for API errors."""

    @app.errorhandler(HTTPException)
    def handle_http_error(error):
        return jsonify({"error": error.description}), error.code

    @app.errorhandler(ValueError)
    def handle_value_error(error):
        return jsonify({"error": str(error)}), 400

    @app.errorhandler(LookupError)
    def handle_lookup_error(error):
        return jsonify({"error": str(error)}), 404

    @app.errorhandler(RuntimeError)
    def handle_runtime_error(error):
        return jsonify({"error": str(error)}), 409

    @app.errorhandler(IntegrityError)
    def handle_integrity_error(error):
        return jsonify({"error": "The request conflicts with existing data."}), 409

    @app.errorhandler(Exception)
    def handle_unexpected_error(error):
        app.logger.exception("Unhandled application error", exc_info=error)
        return jsonify({"error": "Internal server error."}), 500
