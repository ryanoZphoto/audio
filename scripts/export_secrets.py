"""Script to export secrets for Railway deployment."""
import sys
import os
from pathlib import Path

# Add the parent directory to Python path
sys.path.append(str(Path(__file__).parent.parent))

from app.utils.local_secrets import LocalSecretsManager

def export_secrets():
    """Export secrets in a Railway-compatible format."""
    secrets_manager = LocalSecretsManager()
    secrets = secrets_manager.get_all_secrets()
    
    print("\nRailway Environment Variables:")
    print("-----------------------------")
    for key, value in secrets.items():
        # Convert secret file names back to environment variable names
        env_key = key.upper().replace('-', '_')
        print(f"{env_key}={value}")
    
    print("\nInstructions:")
    print("1. Copy these environment variables")
    print("2. Go to your Railway project dashboard")
    print("3. Click on Variables")
    print("4. Click 'New Variable' and paste all variables")
    print("\nNote: Make sure to keep these values secure and never commit them to version control!")

if __name__ == "__main__":
    export_secrets() 