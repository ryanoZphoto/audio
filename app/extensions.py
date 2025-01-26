"""Flask extensions initialization."""
import logging
from flask_sqlalchemy import SQLAlchemy
from flask_caching import Cache
from flask_login import LoginManager
from sqlalchemy import event
from sqlalchemy.engine import Engine
from sqlalchemy.exc import OperationalError
from app.utils.config_utils import get_secret

logger = logging.getLogger(__name__)

# Initialize database with
db = SQLAlchemy()

# Configure Redis cache with secrets
cache = Cache()

# Initialize login manager
login_manager = LoginManager()
login_manager.login_view = 'auth.login'

# Log Redis configuration
logger.info("=== Redis Configuration ===")
logger.info(f"Redis URL: {get_secret('REDIS_URL')}")

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
        if not connection_record.connection._closed:
            logger.info("Connection is still valid")
        else:
            logger.warning("Connection was closed")
    except Exception as e:
        logger.error(f"Error checking connection state: {e}")

# Keep existing code but ensure db is properly exported
__all__ = ['db', 'cache', 'login_manager']
