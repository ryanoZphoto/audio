# Secrets Management Guide

## Overview

This guide explains how to use the secrets management system in the application. The system provides a secure way to store and access sensitive information like API keys, database credentials, and other secrets.

## How It Works

The secrets management system uses two layers:
1. Encrypted files stored in `.secrets/` directory
2. Environment variables as fallback

### Key Features

- Secure encryption of secrets using Fernet (symmetric encryption)
- Automatic fallback to environment variables
- Easy-to-use API for storing and retrieving secrets
- Support for development and production environments

## Usage Guide

### 1. Initializing Secrets

To initialize the secrets system:

```bash
# Create .env file with required variables
cp .env.example .env

# Initialize secrets from environment variables
python scripts/init_local_secrets.py

# Verify environment
python scripts/check_env.py
```

### 2. Storing Secrets

```python
from app.utils.config_utils import get_secrets_manager

# Get singleton instance
secrets_manager = get_secrets_manager()

# Store a new secret
secrets_manager.set_secret('api-key', 'your-secret-value')
```

### 3. Retrieving Secrets

```python
from app.utils.config_utils import get_secret

# Get a secret (tries secrets manager first, then environment variables)
api_key = get_secret('API_KEY')  # Returns None if not found
```

### 4. Using in Services

Example with Payment Service:
```python
from app.utils.config_utils import get_secret

class PaymentService:
    def __init__(self):
        self.stripe_key = get_secret('STRIPE_SECRET_KEY')
        self.webhook_secret = get_secret('STRIPE_WEBHOOK_SECRET')
        
    def process_payment(self, amount):
        stripe.api_key = self.stripe_key
        # Process payment...
```

Example with YouTube Service:
```python
from app.utils.config_utils import get_secret

class YouTubeService:
    def __init__(self):
        self.api_key = get_secret('YOUTUBE_API_KEY')
        
    def search_videos(self, query):
        youtube = build('youtube', 'v3', developerKey=self.api_key)
        # Use API...
```

### 5. Configuration Management

Example configuration class:
```python
from app.utils.config_utils import get_secret

class Config:
    def __init__(self):
        self.SQLALCHEMY_DATABASE_URI = get_secret('DATABASE_URL')
        self.REDIS_URL = get_secret('REDIS_URL')
        self.SECRET_KEY = get_secret('SECRET_KEY')
```

### 6. Security Best Practices

1. Add to .gitignore:
```
.secrets/
.key
.env
```

2. Set proper permissions:
```bash
chmod 600 .secrets/.key
chmod 600 .secrets/
```

### 7. Utility Functions

Export environment variables to secrets:
```python
from app.utils.config_utils import get_secrets_manager

def export_env_to_secrets():
    """Export environment variables to encrypted secrets."""
    secrets_manager = get_secrets_manager()
    secrets = {
        'stripe-secret-key': os.getenv('STRIPE_SECRET_KEY'),
        'database-url': os.getenv('DATABASE_URL'),
        # Add other secrets...
    }
    for key, value in secrets.items():
        if value:
            secrets_manager.set_secret(key, value)
```

Verify required secrets:
```python
from app.utils.config_utils import get_secrets_manager

def verify_secrets():
    """Verify all required secrets are available."""
    secrets_manager = get_secrets_manager()
    all_secrets = secrets_manager.get_all_secrets()
    
    required_secrets = [
        'DATABASE_URL',
        'REDIS_URL',
        'SECRET_KEY',
        'STRIPE_SECRET_KEY',
        # Add other required secrets...
    ]
    
    for secret in required_secrets:
        if secret not in all_secrets:
            print(f"Missing required secret: {secret}")
```

### 8. Environment Separation

The system automatically handles different environments:

```python
if app.config['ENV'] == 'production':
    # Use cloud secrets manager
    pass
else:
    # Use local secrets manager
    pass
```

### 9. Maintenance

Reset secrets storage:
```bash
rm -rf .secrets/
python scripts/init_local_secrets.py
```

Backup secrets:
```python
def backup_secrets():
    """Backup all secrets to a secure location."""
    secrets_manager = get_secrets_manager()
    all_secrets = secrets_manager.get_all_secrets()
    # Implement your backup logic here
```

## Required Secrets

The following secrets are required by the application:

- `DATABASE_URL`: PostgreSQL database connection URL
- `REDIS_URL`: Redis connection URL
- `SECRET_KEY`: Flask application secret key
- `STRIPE_SECRET_KEY`: Stripe API secret key
- `STRIPE_PUBLISHABLE_KEY`: Stripe publishable key
- `STRIPE_WEBHOOK_SECRET`: Stripe webhook secret
- `YOUTUBE_API_KEY`: YouTube API key
- `ADMIN_SECRET`: Admin authentication secret

## Troubleshooting

1. If you see "Secret file not found" warnings:
   - This is normal if the secret isn't in `.secrets/` directory
   - The system will fall back to environment variables

2. If you need to reset the secrets:
   - Delete the `.secrets` directory
   - Run `python scripts/init_local_secrets.py`

3. If encryption key issues occur:
   - Delete `.secrets/.key`
   - The system will generate a new key on next run
