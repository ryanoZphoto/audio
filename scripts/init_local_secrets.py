"""Initialize local secrets from .env file."""
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

from dotenv import load_dotenv
from app.utils.local_secrets import LocalSecretsManager


def main():
    """Main function to initialize secrets."""
    # Load environment variables
    load_dotenv()
    
    # Initialize secrets manager
    secrets_manager = LocalSecretsManager()
    
    # Define secrets to store
    secrets = {
        'stripe-secret-key': os.getenv('STRIPE_SECRET_KEY'),
        'stripe-publishable-key': os.getenv('STRIPE_PUBLISHABLE_KEY'),
        'stripe-webhook-secret': os.getenv('STRIPE_WEBHOOK_SECRET'),
        'youtube-api-key': os.getenv('YOUTUBE_API_KEY'),
        'database-url': os.getenv('DATABASE_URL'),
        'redis-url': os.getenv('REDIS_URL'),
        'flask-secret-key': os.getenv('SECRET_KEY'),
        'token-secret': os.getenv('TOKEN_SECRET')
    }
    
    print("\nInitializing local secrets...")
    print(f"Secrets directory: {secrets_manager.secrets_dir}")
    
    # Store each secret
    success_count = 0
    for secret_id, secret_value in secrets.items():
        if secret_value:
            try:
                secrets_manager.set_secret(secret_id, secret_value)
                print(f"✓ Stored secret: {secret_id}")
                success_count += 1
            except Exception as e:
                print(f"✗ Failed to store {secret_id}: {e}")
        else:
            print(f"⚠ WARNING: No value found for {secret_id}")
    
    print(f"\nSuccessfully stored {success_count} secrets")
    
    # Verify stored secrets
    print("\nVerifying stored secrets...")
    all_secrets = secrets_manager.get_all_secrets()
    for key in all_secrets:
        print(f"✓ Verified: {key}")


if __name__ == "__main__":
    main() 