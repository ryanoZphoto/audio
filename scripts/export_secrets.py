"""Script to export secrets for Railway deployment."""
import sys
import os
from pathlib import Path

# Add the parent directory to Python path
sys.path.append(str(Path(__file__).parent.parent))

from app.utils.local_secrets import LocalSecretsManager
from dotenv import load_dotenv

def export_secrets():
    """Export secrets in a Railway-compatible format."""
    # Load environment variables first
    load_dotenv()
    
    # Initialize secrets manager
    secrets_manager = LocalSecretsManager()
    
    print("\nRailway Environment Variables:")
    print("-----------------------------")
    
    # Get secrets from encrypted storage
    secrets = {
        'STRIPE_SECRET_KEY': secrets_manager.get_secret('stripe-secret-key'),
        'STRIPE_PUBLISHABLE_KEY': secrets_manager.get_secret('stripe-publishable-key'),
        'STRIPE_WEBHOOK_SECRET': secrets_manager.get_secret('stripe-webhook-secret'),
        'YOUTUBE_API_KEY': secrets_manager.get_secret('youtube-api-key'),
        'DATABASE_URL': secrets_manager.get_secret('database-url'),
        'REDIS_URL': secrets_manager.get_secret('redis-url'),
        'SECRET_KEY': secrets_manager.get_secret('flask-secret-key'),
        'TOKEN_SECRET': secrets_manager.get_secret('token-secret')
    }
    
    # Add environment-specific variables
    env_vars = {
        'FLASK_ENV': 'production',
        'FLASK_DEBUG': '0'
    }
    
    # Print all variables that have values
    all_vars = {**secrets, **env_vars}
    for key, value in all_vars.items():
        if value:
            print(f"{key}={value}")
    
    print("\nInstructions:")
    print("1. Copy these environment variables")
    print("2. Go to your Railway project dashboard")
    print("3. Click on Variables")
    print("4. Click 'Raw Editor' and paste all variables")
    print("\nNote: Keep these values secure!")

if __name__ == "__main__":
    export_secrets() 