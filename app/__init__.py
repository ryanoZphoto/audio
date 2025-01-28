import os
import sys
import logging
from flask import Flask
from flask_cors import CORS
from config import Config, TestConfig
from .extensions import init_extensions
from app.tasks.scheduler import init_scheduler

# Configure logging first
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


try:
    logger.info("=== Initializing Flask Application ===")
    logger.info(f"Python version: {sys.version}")
    logger.info(f"Current directory: {os.getcwd()}")
    logger.info("Loading dependencies...")
    logger.info("All dependencies loaded successfully")
except ImportError as e:
    logger.error(f"Failed to import dependency: {e}")
    logger.error("Python path:")
    for path in sys.path:
        logger.error(f"  - {path}")
    raise


def create_app(config_name=None):
    """Create Flask application."""
    try:
        logger.info("=== Initializing Flask Application ===")
        logger.info(f"Python version: {sys.version}")
        logger.info(f"Current directory: {os.getcwd()}")
        logger.info("Loading dependencies...")
        
        # Create Flask app
        app = Flask(__name__, 
                   template_folder='../templates',
                   static_folder='../static')
        
        # Load the appropriate configuration
        if config_name == 'testing':
            app.config.from_object(TestConfig())
        else:
            app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
                'pool_size': 10,
                'pool_timeout': 30,
                'pool_recycle': 1800,
                'max_overflow': 2
            }
            app.config.from_object(Config())
        
        # Configure CORS
        CORS(app, resources={
            r"/*": {
                "origins": ["https://audiosnipt.com", 
                           "http://localhost:5000"],
                "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
                "allow_headers": ["Content-Type", "Authorization"],
                "expose_headers": ["Content-Range"],
                "supports_credentials": True
            }
        })
        
        with app.app_context():
            # Initialize extensions
            init_extensions(app)
            
            # Register blueprints
            from .routes.main import main
            from .routes.search import search_bp
            from .routes.admin_monitor import admin_monitor_bp
            
            app.register_blueprint(main)
            app.register_blueprint(search_bp)
            app.register_blueprint(admin_monitor_bp)
            
            logger.info("All blueprints registered successfully")
            
            # Initialize scheduler in production
            if not app.config['TESTING']:
                init_scheduler()
                logger.info("Background scheduler initialized")
        
        logger.info("Flask application initialized successfully")
        return app
        
    except Exception as e:
        logger.error(f"Error creating application: {e}")
        raise
