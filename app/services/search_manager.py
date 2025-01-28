"""Unified search management service."""
from datetime import datetime, timedelta
import hmac
import hashlib
import logging
from flask import current_app
from app.extensions import db, cache

logger = logging.getLogger(__name__)

def safe_cache_operation(operation):
    """Decorator for safe cache operations with fallback."""
    def wrapper(*args, **kwargs):
        try:
            return operation(*args, **kwargs)
        except Exception as e:
            logger.error(f"Cache operation failed: {str(e)}")
            return None
    return wrapper

class SearchTier:
    """Search tier configuration."""
    FREE = {
        'name': 'free',
        'limit': 3,
        'duration': timedelta(days=1),
        'price': 0
    }
    DAY = {
        'name': 'day',
        'limit': 50,
        'duration': timedelta(days=1),
        'price': 2
    }
    WEEK = {
        'name': 'week',
        'limit': 200,
        'duration': timedelta(days=7),
        'price': 5
    }
    MONTH = {
        'name': 'month',
        'limit': 500,
        'duration': timedelta(days=30),
        'price': 10
    }

class SearchManager:
    """Manages search limits, tokens, and usage tracking."""
    
    def __init__(self):
        """Initialize search manager."""
        self.token_secret = current_app.config.get('TOKEN_SECRET', 'your-secret-key-here')
        self._verify_cache_connection()
        
    def _verify_cache_connection(self):
        """Verify Redis cache connection."""
        try:
            cache.set('_test_key', 'test_value', timeout=1)
            test_result = cache.get('_test_key')
            if test_result != 'test_value':
                logger.error("Cache verification failed - values don't match")
                self._use_fallback = True
            else:
                self._use_fallback = False
        except Exception as e:
            logger.error(f"Cache verification failed: {str(e)}")
            self._use_fallback = True
        
    def _generate_token(self, tier_name, expiry_date, search_limit):
        """Generate a signed token for a search tier."""
        message = f"{tier_name}:{expiry_date}:{search_limit}"
        signature = hmac.new(
            self.token_secret.encode(),
            message.encode(),
            hashlib.sha256
        ).hexdigest()
        return f"{tier_name}:{expiry_date}:{search_limit}:{signature}"
        
    def _validate_token(self, token):
        """Validate a token and return its details."""
        try:
            tier_name, expiry_date, search_limit, signature = token.split(':')
            message = f"{tier_name}:{expiry_date}:{search_limit}"
            expected_signature = hmac.new(
                self.token_secret.encode(),
                message.encode(),
                hashlib.sha256
            ).hexdigest()
            
            if hmac.compare_digest(signature, expected_signature):
                expiry = datetime.fromisoformat(expiry_date)
                if expiry > datetime.utcnow():
                    return {
                        'valid': True,
                        'tier': tier_name,
                        'expiry': expiry,
                        'limit': int(search_limit)
                    }
        except Exception as e:
            logger.error(f"Token validation error: {e}")
        return {'valid': False}
        
    @safe_cache_operation
    def get_free_searches(self, ip_address):
        """Get remaining free searches for an IP address."""
        if self._use_fallback:
            # Fallback to default values if cache is unavailable
            expiry = datetime.utcnow() + SearchTier.FREE['duration']
            return {
                'used': 0,
                'remaining': SearchTier.FREE['limit'],
                'expires': expiry.isoformat()
            }
            
        cache_key = f"free_searches:{ip_address}"
        usage = cache.get(cache_key)
        
        if usage is None:
            expiry = datetime.utcnow() + SearchTier.FREE['duration']
            usage = {
                'used': 0,
                'remaining': SearchTier.FREE['limit'],
                'expires': expiry.isoformat()
            }
            cache.set(cache_key, usage, timeout=86400)
        
        try:
            expiry = datetime.fromisoformat(usage['expires'])
            if expiry < datetime.utcnow():
                expiry = datetime.utcnow() + SearchTier.FREE['duration']
                usage = {
                    'used': 0,
                    'remaining': SearchTier.FREE['limit'],
                    'expires': expiry.isoformat()
                }
                cache.set(cache_key, usage, timeout=86400)
        except (TypeError, ValueError) as e:
            logger.error(f"Invalid expiry format: {e}")
            expiry = datetime.utcnow() + SearchTier.FREE['duration']
            usage = {
                'used': 0,
                'remaining': SearchTier.FREE['limit'],
                'expires': expiry.isoformat()
            }
            cache.set(cache_key, usage, timeout=86400)
        
        return usage
        
    @safe_cache_operation
    def increment_free_usage(self, ip_address):
        """Increment usage count for free tier."""
        if self._use_fallback:
            return True  # Allow searches when cache is down
            
        usage = self.get_free_searches(ip_address)
        if usage and usage['remaining'] > 0:
            usage['used'] += 1
            usage['remaining'] -= 1
            cache.set(f"free_searches:{ip_address}", usage, timeout=86400)
            return True
        return False
        
    def create_subscription_token(self, tier_name):
        """Create a new subscription token."""
        tier = getattr(SearchTier, tier_name.upper(), None)
        if not tier:
            raise ValueError(f"Invalid tier: {tier_name}")
            
        expiry = datetime.utcnow() + tier['duration']
        return self._generate_token(
            tier['name'],
            expiry.isoformat(),
            tier['limit']
        )
        
    def check_subscription(self, token):
        """Check subscription status and remaining searches."""
        if not token:
            return {'valid': False, 'error': 'No token provided'}
            
        token_data = self._validate_token(token)
        if not token_data['valid']:
            return {'valid': False, 'error': 'Invalid token'}
            
        # Get usage from cache
        cache_key = f"token_usage:{token}"
        usage = cache.get(cache_key) or {'used': 0}
        
        remaining = token_data['limit'] - usage['used']
        if remaining <= 0:
            return {'valid': False, 'error': 'Search limit reached'}
            
        return {
            'valid': True,
            'tier': token_data['tier'],
            'used': usage['used'],
            'remaining': remaining,
            'expires': token_data['expiry'].isoformat()
        }
        
    def increment_subscription_usage(self, token):
        """Increment usage count for a subscription."""
        status = self.check_subscription(token)
        if not status['valid']:
            return False
            
        cache_key = f"token_usage:{token}"
        usage = cache.get(cache_key) or {'used': 0}
        usage['used'] += 1
        
        # Store in cache until token expiry
        expiry = datetime.fromisoformat(status['expires'])
        timeout = int((expiry - datetime.utcnow()).total_seconds())
        cache.set(cache_key, usage, timeout=timeout)
        
        return True
        
    def log_search(self, query, success, token=None, ip_address=None):
        """Log search attempt."""
        try:
            log_data = {
                'query': query,
                'success': success,
                'timestamp': datetime.utcnow(),
                'token': token,
                'ip_address': ip_address
            }
            # Store in Redis for analytics
            cache.rpush('search_logs', str(log_data))
            return True
        except Exception as e:
            logger.error(f"Error logging search: {e}")
            return False 