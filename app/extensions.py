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
from urllib.parse import urlparse

logger = logging.getLogger(__name__)

# Initialize extensions without config
db = SQLAlchemy()
migrate = Migrate()
cache = Cache()
login_manager = LoginManager()
mail = Mail()

@login_manager.user_loader
def load_user(user_id):
    """Load user by ID."""
    from app.models import AdminUser
    if not user_id:
        return None
    return AdminUser.query.get(int(user_id))

def init_extensions(app):
    """Initialize all Flask extensions."""
    logger.info("Initializing Flask extensions...")
    
    # Initialize SQLAlchemy
    db.init_app(app)
    
    # Initialize Flask-Migrate
    migrate.init_app(app, db)
    
    # Initialize Flask-Login
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message_category = 'info'
    
    # Initialize Flask-Mail
    mail.init_app(app)
    
    # Configure Redis cache
    redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
    parsed_url = urlparse(redis_url)
    
    # Mask sensitive info in logs
    masked_url = f"{parsed_url.scheme}://{parsed_url.hostname}:{parsed_url.port}{parsed_url.path}"
    logger.info(f"Configuring Redis cache with URL: {masked_url}")
    
    cache_config = {
        'CACHE_TYPE': 'redis',
        'CACHE_REDIS_URL': redis_url,
        'CACHE_DEFAULT_TIMEOUT': 300,
        'CACHE_OPTIONS': {
            'socket_timeout': 2,
            'socket_connect_timeout': 2,
            'retry_on_timeout': True,
            'max_connections': 20,
            'ssl_cert_reqs': None  # Don't verify SSL cert
        }
    }
    
    try:
        with app.app_context():
            cache.init_app(app, config=cache_config)
            # Test connection
            cache.set('_test_key', 'test_value', timeout=1)
            test_result = cache.get('_test_key')
            if test_result != 'test_value':
                raise Exception("Cache test failed - values don't match")
            logger.info("Redis cache initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize Redis cache: {str(e)}")
        logger.warning("Falling back to simple cache")
        # Fallback to simple cache
        app.config['CACHE_TYPE'] = 'simple'
        cache.init_app(app)
    
    # Set up database event listeners
    with app.app_context():
        @event.listens_for(db.engine, 'connect')
        def on_connect(dbapi_connection, connection_record):
            logger.info("Database connection established")
            try:
                cursor = dbapi_connection.cursor()
                cursor.execute("SELECT version()")
                version = cursor.fetchone()[0]
                logger.info(f"Database version: {version}")
                cursor.close()
            except Exception as e:
                logger.error(f"Error getting database version: {e}")

        @event.listens_for(db.engine, 'disconnect')
        def on_disconnect(dbapi_connection, connection_record):
            logger.info("Database connection closed")

    logger.info("Flask extensions initialized successfully")

# Keep existing code but ensure db is properly exported
__all__ = ['db', 'cache', 'login_manager', 'mail']
