import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    """Base configuration class."""
    # Secret key for session management and CSRF protection
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'you-will-never-guess'
    
    # Database configuration
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///' + os.path.join(os.path.abspath(os.path.dirname(__file__)), 'app.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Website hosting directory - where websites will be stored
    WEBSITES_DIRECTORY = os.environ.get('WEBSITES_DIRECTORY') or 'websites'
    
    # CKEditor configuration
    CKEDITOR_SERVE_LOCAL = True
    CKEDITOR_PKG_TYPE = 'full'
    
    # Maximum content size for uploads
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16 MB


class DevelopmentConfig(Config):
    """Development configuration."""
    DEBUG = True
    # More verbose logging
    LOG_LEVEL = 'DEBUG'


class TestingConfig(Config):
    """Testing configuration."""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False
    

class ProductionConfig(Config):
    """Production configuration."""
    DEBUG = False
    LOG_LEVEL = 'INFO'
    # Use stronger security in production
    SESSION_COOKIE_SECURE = True
    REMEMBER_COOKIE_SECURE = True


# Configuration dictionary for app initialization
config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
