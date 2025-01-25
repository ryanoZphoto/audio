"""Database initialization script."""
import os
import sys
import logging
from app.utils.config_utils import get_secret
from app import create_app, db
from app.models import AdminUser

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def init_db():
    """Initialize the database."""
    try:
        app = create_app()
        
        # Verify database URL
        db_url = get_secret('DATABASE_URL')
        if not db_url:
            raise ValueError("DATABASE_URL not configured")
            
        logger.info(f"Initializing database: {db_url}")
        
        with app.app_context():
            db.create_all()
            logger.info("Database initialized successfully")
            
            # Create admin user if none exists
            if not AdminUser.query.first():
                admin_email = os.getenv('ADMIN_EMAIL', 'admin@audiosnipt.com')
                admin_password = os.getenv('ADMIN_PASSWORD', 'AudioSnipt2024!')
                
                admin = AdminUser(email=admin_email)
                admin.set_password(admin_password)
                db.session.add(admin)
                db.session.commit()
                
                logger.info(f"Admin user created: {admin_email}")
            
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    init_db()
