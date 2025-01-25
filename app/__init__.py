import os
import sys
import logging
from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
from config import Config

from .extensions import db, cache, login_manager
from . import models  # Import models after extensions
from app.utils.local_secrets import LocalSecretsManager as SecretsManager

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
    app = Flask(__name__)
    
    # Load configuration
    app.config.from_object(Config())
    
    # Initialize extensions
    db.init_app(app)
    cache.init_app(app)
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
