"""Test script to verify secrets access."""
import os
import sys
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Add project root to Python path
project_root = str(Path(__file__).parent.parent)
sys.path.append(project_root)

from app.utils.config_utils import get_secrets_manager, get_secret


def test_secrets():
    """Test secrets access."""
    print("\nTesting secrets access...")
    
    # Test direct secrets manager access
    secrets_manager = get_secrets_manager()
    all_secrets = secrets_manager.get_all_secrets()
    print("\nSecrets available:")
    for key in all_secrets.keys():
        print(f"✓ {key}")
    
    # Test utility function access
    print("\nTesting secret retrieval:")
    test_keys = [
        'DATABASE_URL',
        'REDIS_URL',
        'SECRET_KEY',  # This will map to flask-secret-key
        'STRIPE_SECRET_KEY'
    ]
    
    for key in test_keys:
        value = get_secret(key)
        if value:
            print(f"✓ Successfully retrieved {key}")
        else:
            print(f"⚠ Failed to retrieve {key}")


if __name__ == "__main__":
    test_secrets() 