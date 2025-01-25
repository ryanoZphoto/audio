import secrets

# Generate a secure secret key
secret_key = secrets.token_hex(32)
print("\nGenerated Secret Key:")
print(secret_key)
print("\nUpdate your .env file with this key for FLASK_SECRET_KEY") 