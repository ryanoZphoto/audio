"""Subscription monitoring tasks."""
import logging
from datetime import datetime, timedelta
from sqlalchemy import and_, or_
from app.models import Subscription
from app.services.email_service import send_email
from app.extensions import db, cache

logger = logging.getLogger(__name__)

def log_task_execution(task_name, success, error=None):
    """Log task execution status."""
    status = "SUCCESS" if success else "FAILED"
    logger.info(f"Task '{task_name}' completed with status: {status}")
    if error:
        logger.error(f"Task '{task_name}' error: {str(error)}")
    # Store execution status in cache for monitoring
    cache.set(
        f"task_status:{task_name}",
        {
            'status': status,
            'last_run': datetime.utcnow().isoformat(),
            'error': str(error) if error else None
        },
        timeout=86400  # 24 hours
    )

def cleanup_expired_subscriptions():
    """Clean up expired subscriptions."""
    task_name = 'cleanup_expired_subscriptions'
    logger.info(f"Starting task: {task_name}")
    try:
        # Find expired subscriptions that are still marked as active
        expired = Subscription.query.filter(
            and_(
                Subscription.status == 'active',
                Subscription.expiry_date < datetime.utcnow()
            )
        ).all()
        
        if not expired:
            logger.info("No expired subscriptions found")
            log_task_execution(task_name, True)
            return
            
        logger.info(f"Found {len(expired)} expired subscriptions")
        
        for sub in expired:
            try:
                # Clear cache
                cache.delete(f"token_usage:{sub.access_token}")
                
                # Update subscription status
                sub.status = 'expired'
                logger.info(f"Marked subscription {sub.id} as expired")
                
                # Notify customer
                if sub.customer and sub.customer.email:
                    send_email(
                        to_email=sub.customer.email,
                        subject="Your subscription has expired",
                        template='emails/subscription_expired.html',
                        context={'subscription': sub}
                    )
            except Exception as sub_error:
                logger.error(
                    f"Error processing subscription {sub.id}: {str(sub_error)}"
                )
                continue
        
        db.session.commit()
        logger.info("Expired subscriptions cleaned up successfully")
        log_task_execution(task_name, True)
        
    except Exception as e:
        logger.error(f"Error cleaning up expired subscriptions: {str(e)}")
        db.session.rollback()
        log_task_execution(task_name, False, e)
        raise

def notify_expiring_subscriptions():
    """Notify customers of soon-to-expire subscriptions."""
    task_name = 'notify_expiring_subscriptions'
    logger.info(f"Starting task: {task_name}")
    try:
        # Find subscriptions expiring in the next 24 hours
        expiring = Subscription.query.filter(
            and_(
                Subscription.status == 'active',
                Subscription.expiry_date > datetime.utcnow(),
                Subscription.expiry_date <= (
                    datetime.utcnow() + timedelta(hours=24)
                )
            )
        ).all()
        
        if not expiring:
            logger.info("No soon-to-expire subscriptions found")
            log_task_execution(task_name, True)
            return
            
        logger.info(f"Found {len(expiring)} soon-to-expire subscriptions")
        
        for sub in expiring:
            try:
                if sub.customer and sub.customer.email:
                    send_email(
                        to_email=sub.customer.email,
                        subject="Your subscription is expiring soon",
                        template='emails/subscription_expiring.html',
                        context={'subscription': sub}
                    )
                    logger.info(
                        f"Sent expiration notice for subscription {sub.id}"
                    )
            except Exception as sub_error:
                logger.error(
                    f"Error notifying subscription {sub.id}: {str(sub_error)}"
                )
                continue
        
        logger.info("Expiration notifications sent successfully")
        log_task_execution(task_name, True)
    
    except Exception as e:
        logger.error(f"Error sending expiration notifications: {str(e)}")
        log_task_execution(task_name, False, e)
        raise

def check_subscription_health():
    """Check overall health of subscription system."""
    task_name = 'check_subscription_health'
    logger.info(f"Starting task: {task_name}")
    try:
        issues = []
        
        # Check for subscriptions with invalid data
        invalid = Subscription.query.filter(
            or_(
                Subscription.plan_type.is_(None),
                Subscription.expiry_date.is_(None),
                Subscription.search_limit.is_(None)
            )
        ).all()
        
        if invalid:
            logger.error(f"Found {len(invalid)} subscriptions with invalid data")
            for sub in invalid:
                issue = {
                    'type': 'invalid_data',
                    'subscription_id': sub.id,
                    'description': []
                }
                
                if sub.plan_type is None:
                    issue['description'].append('missing plan type')
                if sub.expiry_date is None:
                    issue['description'].append('missing expiry date')
                if sub.search_limit is None:
                    issue['description'].append('missing search limit')
                    
                issue['description'] = ', '.join(issue['description'])
                issues.append(issue)
            
        # Check for inconsistencies between DB and cache
        active = Subscription.query.filter_by(status='active').all()
        for sub in active:
            try:
                cache_key = f"token_usage:{sub.access_token}"
                if not cache.get(cache_key):
                    logger.warning(
                        f"Active subscription {sub.id} missing from cache"
                    )
                    issues.append({
                        'type': 'cache_missing',
                        'subscription_id': sub.id,
                        'description': 'subscription missing from cache'
                    })
            except Exception as sub_error:
                logger.error(
                    f"Error checking subscription {sub.id}: {str(sub_error)}"
                )
                continue
                
        logger.info("Subscription health check completed")
        log_task_execution(task_name, True)
        return issues
            
    except Exception as e:
        logger.error(f"Error during subscription health check: {str(e)}")
        log_task_execution(task_name, False, e)
        raise 