from datetime import datetime
from app.models import db, Subscription, SearchLog
import stripe
from app.utils.config_utils import get_secret

def init_stripe():
    """Initialize Stripe with secret key."""
    stripe.api_key = get_secret('STRIPE_SECRET_KEY')
    if not stripe.api_key:
        raise ValueError("STRIPE_SECRET_KEY not configured")

def create_subscription(customer_id: str, price_id: str):
    """Create a new subscription."""
    init_stripe()
    return stripe.Subscription.create(
        customer=customer_id,
        items=[{"price": price_id}]
    )

def check_subscription_status(token):
    """Check if a subscription is valid and has available searches"""
    try:
        plan_type, expiry_date, search_limit, signature = token.split(':')
        expiry = datetime.fromisoformat(expiry_date)
        
        # Find active subscription
        subscription = Subscription.query.filter_by(
            plan_type=plan_type,
            status='active'
        ).first()
        
        if not subscription:
            return False, "No active subscription found"
        
        # Check if subscription has expired
        if datetime.now() > expiry:
            subscription.status = 'expired'
            db.session.commit()
            return False, "Subscription has expired"
        
        # Check search limit
        if subscription.searches_used >= subscription.search_limit:
            return False, "Search limit reached"
        
        return True, subscription
        
    except Exception as e:
        return False, str(e)


def increment_search_count(subscription, query, success=True):
    """Increment the search count for a subscription"""
    try:
        # Log the search
        search_log = SearchLog(
            subscription_id=subscription.id,
            search_query=query,
            success=success
        )
        db.session.add(search_log)
        
        # Increment search count
        subscription.searches_used += 1
        db.session.commit()
        
        return True, None
    except Exception as e:
        return False, str(e)


def get_subscription_stats(subscription_id):
    """Get statistics for a subscription"""
    subscription = Subscription.query.get(subscription_id)
    if not subscription:
        return None
    
    stats = {
        'plan_type': subscription.plan_type,
        'status': subscription.status,
        'searches_used': subscription.searches_used,
        'search_limit': subscription.search_limit,
        'expiry_date': subscription.expiry_date,
        'is_recurring': subscription.is_recurring,
        'remaining_searches': (
            subscription.search_limit - subscription.searches_used
        )
    }
    
    return stats


def check_subscription_renewal(subscription):
    """Check if a subscription needs renewal"""
    if not subscription.is_recurring:
        return False
    
    # Check if expiry is within 24 hours
    time_to_expiry = subscription.expiry_date - datetime.now()
    if time_to_expiry.total_seconds() <= 86400:  # 24 hours in seconds
        return True
    
    return False 
