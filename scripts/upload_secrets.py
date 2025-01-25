"""Utility script to upload secrets to Google Cloud Secret Manager."""

import os
from google.cloud import secretmanager
from dotenv import load_dotenv

def create_secret(client, project_id, secret_id, secret_value):
    """Create a new secret with the given ID and value."""
    try:
        # Create the secret
        parent = f"projects/{project_id}"
        
        # Create the secret object
        client.create_secret(
            request={
                "parent": parent,
                "secret_id": secret_id,
                "secret": {"replication": {"automatic": {}}},
            }
        )
        
        # Add the secret version
        parent = client.secret_path(project_id, secret_id)
        payload = secret_value.encode('UTF-8')
        
        client.add_secret_version(
            request={
                "parent": parent,
                "payload": {"data": payload},
            }
        )
        print(f"Successfully created secret: {secret_id}")
    except Exception as e:
        print(f"Error creating secret {secret_id}: {e}")

def main():
    """Main function to upload secrets."""
    # Load environment variables
    load_dotenv()
    
    # Initialize the client
    client = secretmanager.SecretManagerServiceClient()
    project_id = os.getenv('GOOGLE_CLOUD_PROJECT')
    
    if not project_id:
        print("ERROR: GOOGLE_CLOUD_PROJECT environment variable not set")
        return
    
    # Define secrets to upload
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
    
    # Upload each secret
    for secret_id, secret_value in secrets.items():
        if secret_value:
            create_secret(client, project_id, secret_id, secret_value)
        else:
            print(f"WARNING: No value found for {secret_id}")

if __name__ == "__main__":
    main() 