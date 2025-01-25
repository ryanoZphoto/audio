"""Configuration utility functions."""
import os
from typing import Optional
from app.utils.local_secrets import LocalSecretsManager
import logging


# Singleton instance of secrets manager
_secrets_manager = None


def get_secrets_manager() -> LocalSecretsManager:
    """Get or create the secrets manager instance."""
    global _secrets_manager
    if _secrets_manager is None:
        _secrets_manager = LocalSecretsManager()
    return _secrets_manager


def get_secret(name, default=None):
    """
    Get a secret value from either secrets manager or environment.
    
    Args:
        name: The secret name to retrieve
        default: The default value to return if the secret is not found
        
    Returns:
        The secret value or the default value if not found
    """
    # Map environment variable names to secret file names
    secret_mappings = {
        'SECRET_KEY': 'flask-secret-key',
        # Add other mappings if needed
    }
    
    # Try secrets manager first, fall back to environment variables
    secrets_manager = get_secrets_manager()
    secret_id = secret_mappings.get(name) or name.lower().replace('_', '-')
    value = secrets_manager.get_secret(secret_id)
    
    if not value:
        value = os.getenv(name, default)
        logging.warning(f"Using ENV fallback for {name}")
    
    return value


def normalize_key(key: str) -> str:
    """
    Normalize a key for consistent storage and retrieval.
    
    Args:
        key: The key to normalize
        
    Returns:
        Normalized key string
    """
    return key.lower().replace('_', '-') 