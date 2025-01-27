"""Flask extensions initialization."""
import logging
import os
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_caching import Cache
from flask_login import LoginManager
from flask_mail import Mail
from sqlalchemy import event
from sqlalchemy.engine import Engine

logger = logging.getLogger(__name__)

# Initialize database
db = SQLAlchemy()
migrate = Migrate()

# Initialize cache without config
cache = Cache()

# Initialize login manager
login_manager = LoginManager()
login_manager.login_view = 'auth.login'

# Initialize mail
mail = Mail()

@login_manager.user_loader
def load_user(user_id):
    """Load user by ID."""
    from app.models import AdminUser
    if not user_id:
        return None
    return AdminUser.query.get(int(user_id))

# Log Redis configuration
logger.info("=== Redis Configuration ===")
logger.info(f"Redis URL: {os.getenv('REDIS_URL')}")

@event.listens_for(Engine, "connect")
def connect(dbapi_connection, connection_record):
    logger.info("=== Database Connection Event ===")
    logger.info("Database connection established")
    try:
        cursor = dbapi_connection.cursor()
        cursor.execute("SELECT version()")
        version = cursor.fetchone()[0]
        logger.info(f"Database version: {version}")
        cursor.close()
    except Exception as e:
        logger.error(f"Error getting database version: {e}")

@event.listens_for(Engine, "checkout")
def checkout(dbapi_connection, connection_record, connection_proxy):
    logger.info("Database connection checked out")
    try:
        # Verify connection is still alive
        cursor = dbapi_connection.cursor()
        cursor.execute("SELECT 1")
        cursor.close()
    except Exception as e:
        logger.error(f"Error during connection checkout: {e}")
        raise  # Force SQLAlchemy to get a new connection

@event.listens_for(Engine, "checkin")
def checkin(dbapi_connection, connection_record):
    logger.info("Database connection checked in")
    try:
        cursor = dbapi_connection.cursor()
        cursor.execute("SELECT 1")
        cursor.close()
        logger.info("Connection is valid")
    except Exception as e:
        logger.warning("Connection may be closed")
        logger.error(f"Error checking connection: {e}")

def init_extensions(app):
    """Initialize all Flask extensions."""
    logger.info("Initializing Flask extensions...")
    
    # Initialize SQLAlchemy
    db.init_app(app)
    
    # Initialize Flask-Migrate
    migrate.init_app(app, db)
    
    # Initialize Flask-Cache with Redis config
    if not app.config.get('TESTING'):
        cache_config = {
            'CACHE_TYPE': 'redis',
            'CACHE_REDIS_URL': os.getenv('REDIS_URL', 'redis://localhost:6379/0'),
            'CACHE_DEFAULT_TIMEOUT': 300
        }
        logger.info(f"Initializing Redis cache with URL: {cache_config['CACHE_REDIS_URL']}")
        cache.init_app(app, config=cache_config)
    else:
        # Use simple cache for testing
        logger.info("Using simple cache for testing")
        cache.init_app(app, config={'CACHE_TYPE': 'simple'})
    
    # Initialize Flask-Login
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message_category = 'info'
    
    # Initialize Flask-Mail
    mail.init_app(app)
    
    logger.info("Flask extensions initialized successfully")

# Keep existing code but ensure db is properly exported
__all__ = ['db', 'cache', 'login_manager', 'mail']
