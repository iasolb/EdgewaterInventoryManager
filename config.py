"""
Configuration module for Edgewater Inventory Manager
"""

import os
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables
load_dotenv()


class Config:
    """Base configuration class"""

    # Database Configuration
    DB_HOST = os.getenv("DB_HOST", "localhost")
    DB_PORT = int(os.getenv("DB_PORT", 3306))
    DB_USER = os.getenv("MYSQL_USER", "edgewater_user")
    DB_PASSWORD = os.getenv("MYSQL_PASSWORD", "edgewater_pass")
    DB_NAME = os.getenv("MYSQL_DATABASE", "EdgewaterMaster")
    DB_CHARSET = os.getenv("DB_CHARSET", "utf8mb4")

    # SQLAlchemy Database URI
    SQLALCHEMY_DATABASE_URI = (
        f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@"
        f"{DB_HOST}:{DB_PORT}/{DB_NAME}?charset={DB_CHARSET}"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ECHO = False  # Set to True for SQL query logging

    # Application Settings
    APP_NAME = os.getenv("APP_NAME", "Edgewater Inventory Manager")
    APP_ENV = os.getenv("APP_ENV", "development")
    DEBUG = APP_ENV == "development"

    # Security
    SECRET_KEY = os.getenv("SESSION_SECRET", "dev-secret-key-change-in-production")

    # File Upload
    MAX_FILE_SIZE = int(os.getenv("MAX_FILE_SIZE", 10485760))  # 10MB
    UPLOAD_PATH = Path(os.getenv("UPLOAD_PATH", "./uploads"))
    ALLOWED_EXTENSIONS = {"csv", "xlsx", "xls"}

    # Logging
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    LOG_FILE = Path(os.getenv("LOG_FILE", "./logs/app.log"))

    # Backup
    BACKUP_PATH = Path(os.getenv("BACKUP_PATH", "./backups"))
    BACKUP_RETENTION_DAYS = int(os.getenv("BACKUP_RETENTION_DAYS", 30))

    @classmethod
    def init_app(cls):
        """Initialize application directories"""
        cls.UPLOAD_PATH.mkdir(parents=True, exist_ok=True)
        cls.LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
        cls.BACKUP_PATH.mkdir(parents=True, exist_ok=True)

    @classmethod
    def get_db_config(cls) -> dict:
        """Get database configuration as dictionary"""
        return {
            "host": cls.DB_HOST,
            "port": cls.DB_PORT,
            "user": cls.DB_USER,
            "password": cls.DB_PASSWORD,
            "database": cls.DB_NAME,
            "charset": cls.DB_CHARSET,
        }


class DevelopmentConfig(Config):
    """Development configuration"""

    DEBUG = True
    SQLALCHEMY_ECHO = True  # Enable SQL logging in dev


class ProductionConfig(Config):
    """Production configuration"""

    DEBUG = False
    SQLALCHEMY_ECHO = False

    @classmethod
    def init_app(cls):
        super().init_app()
        # Add production-specific initialization
        if cls.SECRET_KEY == "dev-secret-key-change-in-production":
            raise ValueError("Must set SESSION_SECRET in production!")


class TestingConfig(Config):
    """Testing configuration"""

    TESTING = True
    DB_NAME = os.getenv("TEST_DB_NAME", "EdgewaterMaster_test")
    SQLALCHEMY_DATABASE_URI = (
        f"mysql+pymysql://{Config.DB_USER}:{Config.DB_PASSWORD}@"
        f"{Config.DB_HOST}:{Config.DB_PORT}/{DB_NAME}?charset={Config.DB_CHARSET}"
    )


# Configuration dictionary
config = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
    "testing": TestingConfig,
    "default": DevelopmentConfig,
}


def get_config(env: str = None) -> Config:
    """Get configuration object based on environment"""
    if env is None:
        env = os.getenv("APP_ENV", "development")
    return config.get(env, config["default"])
