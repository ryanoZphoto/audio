"""Secret management utilities for the application."""

from google.cloud import secretmanager
import os
from typing import Dict, Optional


class SecretsManager:
    """Handles secret management using Google Cloud Secret Manager."""

    def __init__(self):
        """Initialize the secrets manager client."""
        self.client = secretmanager.SecretManagerServiceClient()
        self.project_id = os.getenv('GOOGLE_CLOUD_PROJECT')

    def get_secret(self, secret_id: str, version_id: str = "latest") -> Optional[str]:
        """
        Retrieve a secret from Google Cloud Secret Manager.
        
        Args:
            secret_id: The ID of the secret to retrieve
            version_id: The version of the secret (default: "latest")
            
        Returns:
            The secret value or None if not found
        """
        try:
            name = (
                f"projects/{self.project_id}/secrets/{secret_id}/"
                f"versions/{version_id}"
            )
            response = self.client.access_secret_version(
                request={"name": name}
            )
            return response.payload.data.decode("UTF-8")
        except Exception as e:
            print(f"Error accessing secret {secret_id}: {e}")
            return None

    def get_all_secrets(self) -> Dict[str, str]:
        """
        Get all application secrets.
        
        Returns:
            Dictionary of secret key-value pairs
        """
        secrets = {
            'STRIPE_SECRET_KEY': self.get_secret('stripe-secret-key'),
            'STRIPE_PUBLISHABLE_KEY': self.get_secret('stripe-publishable-key'),
            'STRIPE_WEBHOOK_SECRET': self.get_secret('stripe-webhook-secret'),
            'YOUTUBE_API_KEY': self.get_secret('youtube-api-key'),
            'DATABASE_URL': self.get_secret('database-url'),
            'REDIS_URL': self.get_secret('redis-url'),
            'SECRET_KEY': self.get_secret('flask-secret-key'),
            'TOKEN_SECRET': self.get_secret('token-secret')
        }
        return {k: v for k, v in secrets.items() if v is not None} 