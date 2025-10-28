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
        "DATABASE_URL", "postgresql://postgres:postgres@db:5432/todo_dev"
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
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL")

    @classmethod
    def init_app(cls, app):
        Config.init_app(app)
        # ✅ ตรวจให้แน่ใจว่ามี DATABASE_URL
        assert os.getenv("DATABASE_URL"), "DATABASE_URL must be set in production"


# ✅ ใช้ชื่อ config_map เพื่อไม่ชนกับชื่อไฟล์
config_map = {
    "development": DevelopmentConfig,
    "testing": TestingConfig,
    "production": ProductionConfig,
    "default": DevelopmentConfig,
}
