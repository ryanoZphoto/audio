import hmac
import hashlib
from datetime import datetime, timedelta
import os

# Token components
plan_type = "basic"
expiry_date = (datetime.utcnow() + timedelta(days=30)).isoformat()
search_limit = "100"

# Create message
message = f"{plan_type}:{expiry_date}:{search_limit}".encode()

# Calculate signature
secret = os.getenv('TOKEN_SECRET', 'your-secret-key-here').encode()
signature = hmac.new(secret, message, hashlib.sha256).hexdigest()

# Create token
token = f"{plan_type}:{expiry_date}:{search_limit}:{signature}"

print(f"Generated Token: {token}") 