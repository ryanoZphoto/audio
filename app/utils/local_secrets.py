"""Local secrets manager for development."""
import os
import logging
from pathlib import Path
from cryptography.fernet import Fernet, InvalidToken
from typing import Dict, Optional, Union

logger = logging.getLogger(__name__)

# Type hint for secret values
SecretValue = Union[str, bytes, None]

class LocalSecretsManager:
    """Local secrets manager implementation."""
    
    def __init__(self) -> None:
        """Initialize the local secrets manager."""
        self.secrets_dir = os.path.join(
            Path(__file__).parent.parent.parent,
            '.secrets'
        )
        os.makedirs(self.secrets_dir, exist_ok=True)
        
        # Get or create encryption key
        key_path = os.path.join(self.secrets_dir, '.key')
        try:
            if os.path.exists(key_path):
                logger.info("Loading existing encryption key...")
                with open(key_path, 'rb') as f:
                    self.key = f.read()
            else:
                logger.info("Generating new encryption key...")
                self.key = Fernet.generate_key()
                with open(key_path, 'wb') as f:
                    f.write(self.key)
            
            self.cipher_suite = Fernet(self.key)
            logger.info("Encryption initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing encryption: {e}")
            raise

        logger.info(f"Secrets directory: {self.secrets_dir}")

    def set_secret(self, secret_id: str, value: str) -> None:
        """Store an encrypted secret."""
        try:
            logger.debug(f"Encrypting secret: {secret_id}")
            encrypted = self.cipher_suite.encrypt(value.encode())
            secret_path = os.path.join(self.secrets_dir, secret_id)
            
            with open(secret_path, 'wb') as f:
                f.write(encrypted)
            logger.info(f"Successfully stored secret: {secret_id}")
            
            # Verify the secret was stored correctly
            verification = self.get_secret(secret_id)
            if verification != value:
                raise ValueError(f"Verification failed for {secret_id}")
            
        except Exception as e:
            logger.error(f"Error storing secret {secret_id}: {e}")
            raise

    def get_secret(self, secret_id: str) -> Optional[str]:
        """Retrieve and decrypt a secret."""
        try:
            secret_path = os.path.join(self.secrets_dir, secret_id)
            if not os.path.exists(secret_path):
                logger.warning(f"Secret file not found: {secret_path}")
                return None
                
            logger.debug(f"Reading secret file: {secret_id}")
            with open(secret_path, 'rb') as f:
                encrypted = f.read()
            
            try:
                decrypted = self.cipher_suite.decrypt(encrypted)
                return decrypted.decode()
            except InvalidToken:
                logger.error(f"Invalid token for {secret_id} - encryption key mismatch")
                return None
                
        except Exception as e:
            logger.error(f"Error accessing secret {secret_id}: {e}")
            return None

    def get_all_secrets(self) -> Dict[str, str]:
        """Get all application secrets."""
        secrets = {}
        try:
            logger.info(f"Reading secrets from: {self.secrets_dir}")
            if not os.path.exists(self.secrets_dir):
                logger.warning("Secrets directory does not exist!")
                return secrets
            
            files = [f for f in os.listdir(self.secrets_dir) if f != '.key']
            logger.info(f"Found {len(files)} secret files")
            
            for secret_file in files:
                value = self.get_secret(secret_file)
                if value:
                    secrets[secret_file.upper()] = value
                    logger.info(f"Successfully loaded secret: {secret_file}")
                else:
                    logger.warning(f"Failed to load secret: {secret_file}")
            
            logger.info(f"Loaded {len(secrets)} secrets")
        except Exception as e:
            logger.error(f"Error reading secrets directory: {e}")
        return secrets 