from datetime import datetime, timedelta
from app.extensions import db
from app.models import Subscription, SearchLog
import stripe
import os
from sqlalchemy import func

# Initialize Stripe with API key
stripe.api_key = os.getenv('STRIPE_SECRET_KEY')

def init_stripe():
    """Initialize Stripe with secret key."""
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


def get_subscription_stats():
    """Get subscription statistics."""
    total_subs = Subscription.query.count()
    active_subs = Subscription.query.filter_by(status='active').count()
    expired_subs = Subscription.query.filter_by(status='expired').count()
    
    # Get revenue in last 30 days
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    recent_subs = Subscription.query.filter(
        Subscription.created_at >= thirty_days_ago
    ).count()
    
    return {
        'total': total_subs,
        'active': active_subs,
        'expired': expired_subs,
        'recent': recent_subs
    }


def check_subscription_renewal(subscription):
    """Check if a subscription needs renewal"""
    if not subscription.is_recurring:
        return False
    
    # Check if expiry is within 24 hours
    time_to_expiry = subscription.expiry_date - datetime.now()
    if time_to_expiry.total_seconds() <= 86400:  # 24 hours in seconds
        return True
    
    return False 
