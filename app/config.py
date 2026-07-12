import os
from datetime import timedelta
from dotenv import load_dotenv

load_dotenv()


class Config:
    """Base configuration."""
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-prod')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', 'sqlite:///freshmart.db')

    # JWT
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY', 'jwt-secret-change-in-prod')
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(seconds=int(os.environ.get('JWT_ACCESS_TOKEN_EXPIRES', 3600)))

    # IBM Watsonx
    IBM_CLOUD_API_KEY = os.environ.get('IBM_CLOUD_API_KEY', '')
    IBM_WATSONX_PROJECT_ID = os.environ.get('IBM_WATSONX_PROJECT_ID', '')
    IBM_WATSONX_URL = os.environ.get('IBM_WATSONX_URL', 'https://us-south.ml.cloud.ibm.com')
    WATSONX_MODEL_ID = os.environ.get('WATSONX_MODEL_ID', 'ibm/granite-3-8b-instruct')

    # Mail
    MAIL_SERVER = os.environ.get('MAIL_SERVER', 'smtp.gmail.com')
    MAIL_PORT = int(os.environ.get('MAIL_PORT', 587))
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS', 'True').lower() == 'true'
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME', '')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD', '')
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_DEFAULT_SENDER', 'FreshMart <noreply@freshmart.com>')

    # File upload
    MAX_CONTENT_LENGTH = int(os.environ.get('MAX_CONTENT_LENGTH', 16 * 1024 * 1024))
    UPLOAD_FOLDER = os.environ.get('UPLOAD_FOLDER', 'app/static/images/products')

    # App settings
    APP_NAME = os.environ.get('APP_NAME', 'FreshMart')
    APP_TAGLINE = os.environ.get('APP_TAGLINE', 'Fresh Groceries Delivered Fast')
    DELIVERY_FEE = float(os.environ.get('DELIVERY_FEE', 49))
    FREE_DELIVERY_THRESHOLD = float(os.environ.get('FREE_DELIVERY_THRESHOLD', 499))
    TAX_RATE = float(os.environ.get('TAX_RATE', 0.05))

    # Session
    PERMANENT_SESSION_LIFETIME = timedelta(seconds=int(os.environ.get('PERMANENT_SESSION_LIFETIME', 86400)))

    # Admin
    ADMIN_EMAIL = os.environ.get('ADMIN_EMAIL', 'admin@freshmart.com')
    ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD', 'admin123')

    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}


class DevelopmentConfig(Config):
    DEBUG = True
    SQLALCHEMY_ECHO = False


class ProductionConfig(Config):
    DEBUG = False
    SQLALCHEMY_ECHO = False


class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'


config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}
