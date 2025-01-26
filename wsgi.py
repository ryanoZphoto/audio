import os
import sys
import logging
from sqlalchemy.sql import text
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

try:
    logger.info("\n=== Starting WSGI Application ===")
    logger.info(f"Current Working Directory: {os.getcwd()}")
    logger.info(f"Python Version: {sys.version}")
    logger.info(f"Environment: {os.getenv('FLASK_ENV', 'production')}")
    logger.info(f"Debug Mode: {os.getenv('FLASK_DEBUG', '0')}")
    
    # Verify environment variables
    required_vars = ['DATABASE_URL', 'SECRET_KEY', 'REDIS_URL']
    missing_vars = [
        var for var in required_vars 
        if not os.getenv(var)
    ]
    if missing_vars:
        raise ValueError(
            f"Missing required environment variables: {missing_vars}"
        )
    
    # Create Flask application instance
    logger.info("Creating Flask application...")
    from app import create_app
    application = create_app()
    app = application  # For Gunicorn
    
    # Application is now fully initialized
    
    # Verify critical components
    with application.app_context():
        # Test database connection
        logger.info("Testing database connection...")
        from app.extensions import db
        db.session.execute(text('SELECT 1'))
        db.session.commit()
        logger.info("Database connection successful")
        
        # Test Redis connection
        logger.info("Testing Redis connection...")
        from app.extensions import cache
        cache.set('startup_test', 'ok')
        if cache.get('startup_test') != 'ok':
            raise RuntimeError("Redis connection test failed")
        logger.info("Redis connection successful")
    
    logger.info("Flask application initialized successfully")
    logger.info(f"Registered blueprints: {list(app.blueprints.keys())}")
    
except Exception as e:
    logger.error(f"Failed to initialize WSGI application: {e}")
    logger.exception("Startup error details:")
    raise

# Development-only logging
if os.getenv('FLASK_ENV') == 'development':
    if not os.path.exists('logs'):
        os.makedirs('logs')
    file_handler = logging.FileHandler('logs/wsgi.log')
    file_handler.setFormatter(logging.Formatter(
        '%(asctime)s [%(levelname)s] %(name)s: %(message)s'
    ))
    logging.getLogger().addHandler(file_handler)

# For development server
if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
