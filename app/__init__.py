import os
from flask import Flask, jsonify
from flask_cors import CORS
from app.models import db
from app.routes import api
from app.config import config


def create_app(config_name=None):
    """Application factory pattern"""
    if config_name is None:
        config_name = os.getenv("FLASK_ENV", "development")

    app = Flask(__name__)
    app.config.from_object(config[config_name])
    config[config_name].init_app(app)

    # ✅ DATABASE_URL (Railway / Local)
    db_url = os.getenv("DATABASE_URL")

    if db_url:
        # Railway uses "postgres://" — convert for SQLAlchemy
        if db_url.startswith("postgres://"):
            db_url = db_url.replace("postgres://", "postgresql+psycopg://", 1)
        elif db_url.startswith("postgresql://"):
            db_url = db_url.replace("postgresql://", "postgresql+psycopg://", 1)

        app.config["SQLALCHEMY_DATABASE_URI"] = db_url
    else:
        # ✅ Fallback for local dev (Docker or native Postgres)
        app.config["SQLALCHEMY_DATABASE_URI"] = (
            "postgresql+psycopg://testuser:testpass@127.0.0.1:5433/testdb"
        )


    # Turn off modification tracking for performance
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    # ✅ Enable CORS for GitHub Pages + Local Dev
    CORS(app, resources={
        r"/api/*": {
            "origins": [
                "http://localhost:3000",
                "http://localhost:5000",
                "https://*.github.io",
                "https://natthapong073.github.io"
            ],
            "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
            "allow_headers": ["Content-Type"],
            "supports_credentials": False
        }
    })

    # ✅ Initialize Database + Register Routes
    db.init_app(app)
    app.register_blueprint(api, url_prefix="/api")

    # ✅ Default route
    @app.route("/")
    def index():
        return jsonify({
            "message": "Flask Todo API",
            "version": "1.0.0",
            "endpoints": {
                "health": "/api/health",
                "todos": "/api/todos"
            }
        })

    # ✅ Error Handlers
    @app.errorhandler(404)
    def not_found(error):
        return jsonify({
            "success": False,
            "error": "Resource not found"
        }), 404

    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        return jsonify({
            "success": False,
            "error": "Internal server error"
        }), 500

    @app.errorhandler(Exception)
    def handle_exception(error):
        """Handle all unhandled exceptions"""
        db.session.rollback()
        return jsonify({
            "success": False,
            "error": str(error) if app.debug else "Internal server error"
        }), 500

    # ✅ Auto-create tables only if not exists
    with app.app_context():
        try:
            db.create_all()
        except Exception as e:
            print(f"⚠️ Database initialization failed: {e}")

    return app
