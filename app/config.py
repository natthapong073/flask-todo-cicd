import os
from dotenv import load_dotenv
from sqlalchemy.pool import StaticPool

# โหลดตัวแปรจาก .env
load_dotenv()


class Config:
    """Base configuration class"""
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key-change-in-production")
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    @staticmethod
    def init_app(app):
        pass


class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = os.getenv(
        # ✅ เปลี่ยนให้ใช้ psycopg driver (รองรับ Python 3.13)
        "DATABASE_URL",
        "postgresql+psycopg://postgres:postgres@db:5432/todo_dev"
    )


class TestingConfig(Config):
    """Testing configuration"""
    TESTING = True
    DEBUG = False
    # ✅ ใช้ SQLite in-memory (ให้ตรงกับ test test_uses_sqlite_memory)
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    WTF_CSRF_ENABLED = False  # ✅ ปิด CSRF ตอนเทสต์
    # ✅ ใช้ StaticPool เพื่อแชร์ connection เดียวกันใน memory
    SQLALCHEMY_ENGINE_OPTIONS = {
        "connect_args": {"check_same_thread": False},
        "poolclass": StaticPool,
    }


class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False

    # ✅ Force psycopg3 driver even if Render gives psycopg2-style URL
    raw_db_url = os.getenv("DATABASE_URL", "")
    if raw_db_url.startswith("postgres://"):
        raw_db_url = raw_db_url.replace("postgres://", "postgresql+psycopg://")
    elif raw_db_url.startswith("postgresql://") and "+psycopg" not in raw_db_url:
        raw_db_url = raw_db_url.replace("postgresql://", "postgresql+psycopg://")

    SQLALCHEMY_DATABASE_URI = raw_db_url

    @classmethod
    def init_app(cls, app):
        Config.init_app(app)
        assert os.getenv("DATABASE_URL"), "DATABASE_URL must be set in production"


# ✅ ใช้ชื่อ config_map เพื่อไม่ชนกับชื่อไฟล์
config_map = {
    "development": DevelopmentConfig,
    "testing": TestingConfig,
    "production": ProductionConfig,
    "default": DevelopmentConfig,
}
