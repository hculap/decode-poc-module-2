import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    """Application configuration settings."""
    
    # Flask settings
    SECRET_KEY = os.getenv('SECRET_KEY', os.urandom(24).hex())
    DEBUG = os.getenv('FLASK_ENV') == 'development'
    
    # Database
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URI', 'sqlite:///fireflies.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_pre_ping": True,
        "pool_size": 10,
        "max_overflow": 20,
        "pool_recycle": 1800,
    }
    
    # Fireflies.ai
    FIREFLIES_API_URL = "https://api.fireflies.ai/graphql"
    FIREFLIES_API_KEY = os.getenv("FIREFLIES_API_KEY")
    
    # Webhook
    FIREFLIES_WEBHOOK_SECRET = os.getenv("FIREFLIES_WEBHOOK_SECRET", "")
    VERIFY_SIGNATURE = bool(FIREFLIES_WEBHOOK_SECRET)
    
    # Logging
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
