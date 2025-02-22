"""Configuration settings for the application."""
import os
import sys
import logging
from dotenv import load_dotenv

logger = logging.getLogger(__name__)


class Config:
    """Application configuration class."""
    
    def __init__(self):
        """Initialize configuration with environment variables."""
        logger.info("=== Loading Configuration ===")
        
        # Load database configuration
        self.SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL')
        if not self.SQLALCHEMY_DATABASE_URI:
            raise ValueError("DATABASE_URL is required")
            
        # Load Redis configuration
        self.REDIS_URL = os.getenv('REDIS_URL')
        if not self.REDIS_URL:
            raise ValueError("REDIS_URL is required")
            
        # Load application secrets
        self.SECRET_KEY = os.getenv('SECRET_KEY')
        if not self.SECRET_KEY:
            raise ValueError("SECRET_KEY is required")
            
        # Load Stripe configuration
        self.STRIPE_SECRET_KEY = os.getenv('STRIPE_SECRET_KEY')
        self.STRIPE_PUBLISHABLE_KEY = os.getenv('STRIPE_PUBLISHABLE_KEY')
        self.STRIPE_WEBHOOK_SECRET = os.getenv('STRIPE_WEBHOOK_SECRET')
        
        # Load YouTube configuration
        self.YOUTUBE_API_KEY = os.getenv('YOUTUBE_API_KEY')
        
        # Email configuration
        self.MAIL_SERVER = os.getenv('MAIL_SERVER', 'smtp.gmail.com')
        self.MAIL_PORT = int(os.getenv('MAIL_PORT', 587))
        self.MAIL_USE_TLS = os.getenv('MAIL_USE_TLS', 'True').lower() == 'true'
        self.MAIL_USERNAME = os.getenv('MAIL_USERNAME')
        self.MAIL_PASSWORD = os.getenv('MAIL_PASSWORD')
        self.MAIL_DEFAULT_SENDER = os.getenv('MAIL_DEFAULT_SENDER')
        
        # Additional configuration
        self.SQLALCHEMY_TRACK_MODIFICATIONS = False
        self.SESSION_COOKIE_SECURE = True
        self.SESSION_COOKIE_HTTPONLY = True
        self.SESSION_COOKIE_SAMESITE = 'Lax'
        self.SERVER_NAME = 'audiosnipt.com'

        # Log environment information
        logger.info("=== Loading Configuration ===")
        logger.info(f"Current Working Directory: {os.getcwd()}")
        logger.info(f"Python Version: {sys.version}")
        logger.info(f"Environment: {os.getenv('FLASK_ENV', 'production')}")
        
        # Load and validate database URL
        if not self.SQLALCHEMY_DATABASE_URI:
            logger.error("DATABASE_URL not set!")
            raise ValueError("DATABASE_URL environment variable is required")
        
        logger.info("Database URL format validation...")
        logger.info(f"Original DATABASE_URL: {self.SQLALCHEMY_DATABASE_URI}")
        
        # Parse and validate database URL components
        try:
            # Fix Postgres URL if needed
            if self.SQLALCHEMY_DATABASE_URI:
                # Convert postgres:// to postgresql://
                if self.SQLALCHEMY_DATABASE_URI.startswith('postgres://'):
                    self.SQLALCHEMY_DATABASE_URI = (
                        self.SQLALCHEMY_DATABASE_URI.replace(
                            'postgres://', 'postgresql://', 1
                        )
                    )
                    logger.info("Converted postgres:// to postgresql://")
                
                # Ensure URL starts with postgresql://
                if not self.SQLALCHEMY_DATABASE_URI.startswith(
                    'postgresql://'
                ):
                    self.SQLALCHEMY_DATABASE_URI = (
                        f"postgresql://{self.SQLALCHEMY_DATABASE_URI}"
                    )
                    logger.info("Added postgresql:// prefix to database URL")
                
                # Handle Railway's database URL format
                if 'monorail.proxy.rlwy.net' in self.SQLALCHEMY_DATABASE_URI:
                    parts = self.SQLALCHEMY_DATABASE_URI.split('@')
                    if len(parts) == 2:
                        auth = parts[0]
                        host_port = parts[1].split('/')[0]
                        db_name = parts[1].split('/')[-1]
                        
                        # Reconstruct the URL with the correct format, ensuring postgresql:// prefix
                        if not auth.startswith('postgresql://'):
                            auth = 'postgresql://' + auth.replace('postgresql://', '')
                        self.SQLALCHEMY_DATABASE_URI = f"{auth}@{host_port}/{db_name}"
                        logger.info("Reformatted Railway database URL")
                
                # Validate URL format
                if not any(
                    self.SQLALCHEMY_DATABASE_URI.startswith(prefix)
                    for prefix in ['postgresql://', 'mysql://', 'sqlite://']
                ):
                    raise ValueError(
                        "Invalid database URL scheme. Must start with "
                        "postgresql://, mysql://, or sqlite://"
                    )
            
            # Log sanitized URL (hide password)
            sanitized_url = self.SQLALCHEMY_DATABASE_URI
            if '@' in sanitized_url:
                # Extract password section
                auth_section = sanitized_url.split('@')[0]
                if ':' in auth_section:
                    # Replace password with ***
                    sanitized_url = sanitized_url.replace(
                        auth_section.split(':')[1].split('@')[0],
                        '***'
                    )
            logger.info(f"Sanitized DATABASE_URL: {sanitized_url}")
            
        except Exception as e:
            logger.error(f"Error validating database URL: {str(e)}")
            raise ValueError(f"Invalid database URL format: {str(e)}")
        
        # Load other configuration
        if not self.SECRET_KEY:
            logger.warning(
                "SECRET_KEY not set! Using default "
                "(not recommended for production)"
            )
            self.SECRET_KEY = 'default-secret-key'
        
        # Upload folder for clips
        self.UPLOAD_FOLDER = 'clips'
        if not os.path.exists(self.UPLOAD_FOLDER):
            logger.info(f"Creating upload folder: {self.UPLOAD_FOLDER}")
            os.makedirs(self.UPLOAD_FOLDER, exist_ok=True)

        # Session configuration
        self.SESSION_COOKIE_DOMAIN = os.getenv('SESSION_COOKIE_DOMAIN')
        if self.SESSION_COOKIE_DOMAIN:
            logger.info(
                f"Using custom session cookie domain: "
                f"{self.SESSION_COOKIE_DOMAIN}"
            )
        
        # Add to Config class
        self.AI_MODEL_CACHE = os.path.join(os.getcwd(), 'ai_models')
        if not os.path.exists(self.AI_MODEL_CACHE):
            os.makedirs(self.AI_MODEL_CACHE)
        
        # Add to Config class
        self.AI_MODEL_VERSION = "distilbert-base-cased-distilled-squad-v1.1"
        
        # Admin token for monitoring
        self.ADMIN_TOKEN = os.environ.get('ADMIN_TOKEN', 'your-secure-admin-token')
        
        logger.info("Configuration loaded successfully")

    def _validate_config(self):
        if not self.SQLALCHEMY_DATABASE_URI:
            logger.error("DATABASE_URL not set!")
            raise ValueError("DATABASE_URL environment variable is required")
        if not self.REDIS_URL:
            logger.error("REDIS_URL not set!")
            raise ValueError("REDIS_URL environment variable is required")
        if not self.SECRET_KEY:
            logger.error("SECRET_KEY not set!")
            raise ValueError("SECRET_KEY environment variable is required")
        if not self.STRIPE_SECRET_KEY:
            logger.error("STRIPE_SECRET_KEY not set!")
            raise ValueError("STRIPE_SECRET_KEY environment variable is required")
        if not self.STRIPE_PUBLISHABLE_KEY:
            logger.error("STRIPE_PUBLISHABLE_KEY not set!")
            raise ValueError("STRIPE_PUBLISHABLE_KEY environment variable is required")
        if not self.YOUTUBE_API_KEY:
            logger.error("YOUTUBE_API_KEY not set!")
            raise ValueError("YOUTUBE_API_KEY environment variable is required")


class TestConfig:
    """Testing configuration."""
    
    def __init__(self):
        """Initialize test configuration."""
        # Load environment variables
        load_dotenv()
        
        # Database configuration
        self.SQLALCHEMY_DATABASE_URI = os.getenv('TEST_DATABASE_URL', 'sqlite:///:memory:')
        self.SQLALCHEMY_TRACK_MODIFICATIONS = False
        
        # Redis configuration
        self.REDIS_URL = os.getenv('TEST_REDIS_URL', os.getenv('REDIS_URL'))
        
        # Application configuration
        self.TESTING = True
        self.SECRET_KEY = os.getenv('SECRET_KEY')
        self.WTF_CSRF_ENABLED = False
        self.SESSION_COOKIE_SECURE = False
        self.SERVER_NAME = 'audiosnipt.com'
        
        # Stripe configuration
        self.STRIPE_SECRET_KEY = os.getenv('STRIPE_SECRET_KEY')
        self.STRIPE_PUBLISHABLE_KEY = os.getenv('STRIPE_PUBLISHABLE_KEY')
        self.STRIPE_WEBHOOK_SECRET = os.getenv('STRIPE_WEBHOOK_SECRET')
        
        # YouTube configuration
        self.YOUTUBE_API_KEY = os.getenv('YOUTUBE_API_KEY')
        
        # Email configuration
        self.MAIL_SUPPRESS_SEND = True
