"""Check environment variables."""
import os
from dotenv import load_dotenv

def check_env():
    """Check if required environment variables are set."""
    load_dotenv()
    
    required_vars = [
        'STRIPE_SECRET_KEY',
        'STRIPE_PUBLISHABLE_KEY',
        'STRIPE_WEBHOOK_SECRET',
        'YOUTUBE_API_KEY',
        'DATABASE_URL',
        'REDIS_URL',
        'SECRET_KEY',
        'TOKEN_SECRET'
    ]
    
    print("\nChecking environment variables...")
    missing = []
    for var in required_vars:
        value = os.getenv(var)
        if value:
            print(f"✓ {var} is set")
        else:
            print(f"✗ {var} is missing")
            missing.append(var)
    
    if missing:
        print("\nMissing variables:")
        for var in missing:
            print(f"- {var}")
    else:
        print("\nAll required variables are set!")

if __name__ == "__main__":
    check_env() 