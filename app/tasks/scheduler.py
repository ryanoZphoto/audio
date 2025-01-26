"""Task scheduler module."""
import logging
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from app.tasks.subscription_monitor import (
    cleanup_expired_subscriptions,
    notify_expiring_subscriptions,
    check_subscription_health
)

logger = logging.getLogger(__name__)


def init_scheduler():
    """Initialize and start the task scheduler."""
    scheduler = BackgroundScheduler()
    
    # Add jobs
    scheduler.add_job(
        func=cleanup_expired_subscriptions,
        trigger=CronTrigger(hour='*'),  # Every hour
        id='cleanup_expired_subscriptions',
        name='Clean up expired subscriptions',
        replace_existing=True
    )
    
    scheduler.add_job(
        func=notify_expiring_subscriptions,
        trigger=CronTrigger(hour=0),  # Daily at midnight
        id='notify_expiring_subscriptions',
        name='Notify users of expiring subscriptions',
        replace_existing=True
    )
    
    scheduler.add_job(
        func=check_subscription_health,
        trigger=CronTrigger(hour='*/6'),  # Every 6 hours
        id='check_subscription_health',
        name='Check subscription system health',
        replace_existing=True
    )
    
    # Start scheduler
    scheduler.start()
    logger.info("Task scheduler started")
    
    return scheduler 