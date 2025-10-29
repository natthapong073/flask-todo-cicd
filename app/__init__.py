import os
from flask import Flask, jsonify
from flask_cors import CORS
from app.models import db
from app.routes import api
from app.config import config


def create_app(config_name=None):
    """Application factory pattern"""
    if config_name is None:
        config_name = os.getenv('FLASK_ENV', 'development')

    app = Flask(__name__)
    app.config.from_object(config[config_name])
    config[config_name].init_app(app)

    # ✅ Check environment for Database URL (Railway / Local)
    db_url = os.getenv("DATABASE_URL")
    if db_url:
        # Railway ให้ URL ที่ขึ้นต้นด้วย postgres:// ต้องแก้เป็น postgresql://
        if db_url.startswith("postgres://"):
            db_url = db_url.replace("postgres://", "postgresql+psycopg://", 1)
        elif db_url.startswith("postgresql://"):
            db_url = db_url.replace("postgresql://", "postgresql+psycopg://", 1)

        app.config["SQLALCHEMY_DATABASE_URI"] = db_url
    else:
        # ✅ Fallback local (ถ้าไม่มี DATABASE_URL ใน env)
        app.config["SQLALCHEMY_DATABASE_URI"] = (
            "postgresql+psycopg://testuser:testpass@localhost:5433/testdb"
        )

    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    # ✅ Enable CORS for GitHub Pages + Local Development
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

    # ✅ Initialize database and register routes
    db.init_app(app)
    app.register_blueprint(api, url_prefix='/api')

    # ✅ Default route
    @app.route('/')
    def index():
        return jsonify({
            'message': 'Flask Todo API',
            'version': '1.0.0',
            'endpoints': {
                'health': '/api/health',
                'todos': '/api/todos'
            }
        })

    # ✅ Error handlers
    @app.errorhandler(404)
    def not_found(error):
        return jsonify({
            'success': False,
            'error': 'Resource not found'
        }), 404

    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': 'Internal server error'
        }), 500

    @app.errorhandler(Exception)
    def handle_exception(error):
        """Handle all unhandled exceptions"""
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': 'Internal server error'
        }), 500

    # ✅ Create all tables if not exist
    with app.app_context():
        db.create_all()

    return app
