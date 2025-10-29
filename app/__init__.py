import os
from flask import Flask, jsonify
from app.models import db
from app.routes import api
from app.config import config_map  # ✅ ใช้ config_map จาก config.py


def create_app(config_name=None):
    """Application factory pattern"""
    # ✅ ตรวจค่าการทำงานเริ่มต้น
    if config_name is None:
        config_name = os.getenv("FLASK_ENV", "development")

    app = Flask(__name__)

    # ✅ แก้ Render issue: DATABASE_URL ยังเป็น driver เก่า (postgresql://)
    if os.getenv("DATABASE_URL") and "psycopg" not in os.getenv("DATABASE_URL"):
        fixed_url = os.getenv("DATABASE_URL").replace("postgres://", "postgresql+psycopg://")
        fixed_url = fixed_url.replace("postgresql://", "postgresql+psycopg://")
        os.environ["DATABASE_URL"] = fixed_url

    # ✅ โหลด config
    app.config.from_object(config_map.get(config_name, config_map["default"]))
    config_map.get(config_name, config_map["default"]).init_app(app)

    # ✅ เชื่อมต่อฐานข้อมูล
    db.init_app(app)

    # ✅ Register blueprints
    app.register_blueprint(api, url_prefix="/api")

    # ✅ Root endpoint
    @app.route("/")
    def index():
        return jsonify(
            {
                "message": "Flask Todo API",
                "version": "1.0.0",
                "endpoints": {"health": "/api/health", "todos": "/api/todos"},
            }
        )

    # ✅ Error Handlers
    @app.errorhandler(404)
    def not_found(error):
        return jsonify({"success": False, "error": "Resource not found"}), 404

    @app.errorhandler(500)
    def internal_error(error):
        return jsonify({"success": False, "error": "Internal server error"}), 500

    @app.errorhandler(Exception)
    def handle_exception(error):
        """Handle all unhandled exceptions"""
        db.session.rollback()
        return jsonify({"success": False, "error": "Internal server error"}), 500

    # ✅ สร้างตารางเฉพาะตอนที่ไม่ใช่ testing (กัน pytest พัง)
    if not app.config.get("TESTING", False):
        with app.app_context():
            # ล้าง todos ออกถ้ามีอยู่แล้ว (ป้องกัน duplicate)
            from sqlalchemy import text
            try:
                db.session.execute(text("DROP TABLE IF EXISTS todos CASCADE;"))
                db.session.commit()
            except Exception as e:
                print("⚠️ Skip cleanup:", e)

            db.create_all()

    return app
