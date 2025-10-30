import os
from flask import Flask, jsonify
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_migrate import Migrate
from sqlalchemy.exc import SQLAlchemyError

from app.models import db
from app.routes import api
from app.config import config
from app.logging_config import setup_logging
from app.swagger import swagger_ui_blueprint, SWAGGER_URL


def create_app(config_name=None):
    """Application factory pattern"""
    app = Flask(__name__, static_folder="static")

    # ✅ โหลด config
    if config_name is None:
        config_name = os.getenv("FLASK_ENV", "development")
    app.config.from_object(config[config_name])
    config[config_name].init_app(app)

    # ✅ Database URL (Railway / Local)
    db_url = os.getenv("DATABASE_URL")
    if db_url:
        if db_url.startswith("postgres://"):
            db_url = db_url.replace("postgres://", "postgresql+psycopg://", 1)
        elif db_url.startswith("postgresql://"):
            db_url = db_url.replace("postgresql://", "postgresql+psycopg://", 1)
        app.config["SQLALCHEMY_DATABASE_URI"] = db_url
    else:
        app.config["SQLALCHEMY_DATABASE_URI"] = (
            "postgresql+psycopg://testuser:testpass@127.0.0.1:5433/testdb"
        )

    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    # ✅ Enable CORS
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
        }
    })

    # ✅ Rate Limiter
    limiter = Limiter(
        get_remote_address,
        app=app,
        default_limits=["200 per day", "50 per hour"]
    )

    # ✅ Logging
    logger = setup_logging(app)
    logger.info("🚀 Flask app initialized successfully")

    # ✅ Database + Migration
    db.init_app(app)
    migrate = Migrate(app, db)

    # ✅ Register Blueprints
    app.register_blueprint(api, url_prefix="/api")

    # ✅ Swagger UI
    app.register_blueprint(swagger_ui_blueprint, url_prefix=SWAGGER_URL)

    # ✅ Default route
    @app.route("/")
    def index():
        return jsonify({
            "message": "Flask Todo API",
            "version": "1.0.0",
            "endpoints": {
                "health": "/api/health",
                "todos": "/api/todos",
                "docs": "/docs"
            }
        }), 200

    # ✅ Error Handlers
    @app.errorhandler(404)
    def not_found(error):
        return jsonify({"success": False, "error": "Resource not found"}), 404

    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        return jsonify({"success": False, "error": "Internal server error"}), 500

    @app.errorhandler(Exception)
    def handle_exception(error):
        db.session.rollback()
        return jsonify({
            "success": False,
            "error": str(error) if app.debug else "Internal server error"
        }), 500

    # ✅ Auto-create tables
    with app.app_context():
        try:
            db.create_all()
        except SQLAlchemyError as e:
            logger.warning(f"⚠️ Database initialization failed: {e}")

    return app
