import os
import sys
import logging
from flask import Flask
from flask_cors import CORS
from config import Config
from .extensions import db, cache, login_manager

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


def create_app():
    """Flask application factory."""
    app = Flask(__name__, 
                template_folder='../templates',
                static_folder='../static')
    
    # Load configuration
    app.config.from_object(Config())
    
    # Configure SQLAlchemy before initializing
    app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
        'connect_args': {}
    }
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL').replace('postgresql://', 'postgresql+psycopg2://')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # Initialize extensions
    CORS(app)  # Enable CORS for all routes
    db.init_app(app)
    cache.init_app(app, config={
        'CACHE_TYPE': 'redis',
        'CACHE_REDIS_URL': "redis://default:YsvFnWeygwfKLPLcNMScRohVdMhLhKcm@monorail.proxy.rlwy.net:54967/0",
        'CACHE_REDIS_SSL': True
    })
    login_manager.init_app(app)
    
    # Register main blueprint first to ensure it handles root route
    from .routes import main_bp
    app.register_blueprint(main_bp)
    
    # Initialize admin blueprint
    from app.admin import init_admin
    init_admin(app)
    
    # Register other blueprints
    from .routes import (
        monitoring_bp, search_bp, blog_bp,
        seo_bp, payment_bp, dashboard_bp
    )
    from .auth import auth_bp
    
    app.register_blueprint(auth_bp)
    app.register_blueprint(monitoring_bp)
    app.register_blueprint(search_bp)
    app.register_blueprint(blog_bp)
    app.register_blueprint(seo_bp)
    app.register_blueprint(payment_bp)
    app.register_blueprint(dashboard_bp)
    
    return app
