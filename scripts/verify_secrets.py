"""Verify all secrets are properly configured."""
import sys
import logging
from pathlib import Path

# Add project root to Python path
project_root = str(Path(__file__).parent.parent)
sys.path.append(project_root)

from app.utils.config_utils import get_secret

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

REQUIRED_SECRETS = [
    'DATABASE_URL',
    'REDIS_URL',
    'SECRET_KEY',
    'STRIPE_SECRET_KEY',
    'STRIPE_PUBLISHABLE_KEY',
    'STRIPE_WEBHOOK_SECRET',
    'YOUTUBE_API_KEY',
    'TOKEN_SECRET'
]

def verify_secrets():
    """Check required secrets exist."""
    missing = []
    for secret in REQUIRED_SECRETS:
        value = get_secret(secret)
        if not value:
            missing.append(secret)
            logger.error(f"Missing secret: {secret}")
        else:
            logger.info(f"Found secret: {secret}")
    
    if missing:
        logger.error(f"Missing {len(missing)} secrets: {', '.join(missing)}")
        return False
    
    logger.info("All required secrets are configured!")
    return True

if __name__ == "__main__":
    verify_secrets() 