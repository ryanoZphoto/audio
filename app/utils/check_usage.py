import logging
import os
from models import db, SearchUsage
from app import app

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def ensure_db_directory():
    """Ensure the database directory exists."""
    db_uri = app.config['SQLALCHEMY_DATABASE_URI']
    if db_uri.startswith('sqlite:///'):
        db_path = db_uri.replace('sqlite:///', '')
        db_dir = os.path.dirname(db_path)
        if db_dir and not os.path.exists(db_dir):
            os.makedirs(db_dir)
            logger.info(f"Created database directory: {db_dir}")

def check_token_usage(token):
    """Check usage stats for a given token."""
    try:
        with app.app_context():
            # Ensure database exists
            ensure_db_directory()
            db.create_all()
            
            # Log database path
            db_path = app.config['SQLALCHEMY_DATABASE_URI'].replace('sqlite:///', '')
            logger.info(f"Using database at: {db_path}")
            
            # Query the SearchUsage table
            usage = SearchUsage.query.filter_by(token=token).first()
            
            if usage:
                logger.info("Token found in database")
                logger.info(f"Searches used: {usage.searches_used}")
                logger.info(f"Searches remaining: {usage.searches_remaining}")
                logger.info(f"Last search at: {usage.last_search_at}")
                return usage
            else:
                logger.warning("Token not found in database")
                return None
                
    except Exception as e:
        logger.error(f"Error checking token usage: {str(e)}")
        return None

if __name__ == '__main__':
    test_token = ('basic:2025-02-19T07:26:27.588925:100:'
                 '678110543223855625d15c5802d78acc552ef7c3ac5d9b3bdce9991750b8bfd9')
    check_token_usage(test_token) 