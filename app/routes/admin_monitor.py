"""Admin monitoring routes."""
from flask import Blueprint, render_template, current_app, request, abort
from app.extensions import cache, db
from app.models import Subscription, Customer
from datetime import datetime
from functools import wraps

admin_monitor_bp = Blueprint('admin_monitor', __name__)

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        admin_token = request.args.get('token')
        if not admin_token or admin_token != current_app.config.get('ADMIN_TOKEN'):
            abort(403)
        return f(*args, **kwargs)
    return decorated_function

def get_task_status(task_name):
    """Get status of a scheduled task."""
    status = cache.get(f"task_status:{task_name}")
    if not status:
        return {
            'status': 'Unknown',
            'last_run': 'Never',
            'error': None
        }
    return status

def get_subscription_stats():
    """Get subscription statistics."""
    total = Subscription.query.count()
    active = Subscription.query.filter_by(status='active').count()
    expired = Subscription.query.filter_by(status='expired').count()
    expiring_soon = Subscription.query.filter(
        Subscription.expiry_date <= datetime.utcnow()
    ).count()
    
    return {
        'total': total,
        'active': active,
        'expired': expired,
        'expiring_soon': expiring_soon
    }

@admin_monitor_bp.route('/monitor')
@admin_required
def monitor():
    """Display system monitoring information."""
    # Get task statuses
    tasks = {
        'Cleanup Expired': get_task_status('cleanup_expired_subscriptions'),
        'Send Notifications': get_task_status('notify_expiring_subscriptions'),
        'Health Check': get_task_status('check_subscription_health')
    }
    
    # Get subscription stats
    stats = get_subscription_stats()
    
    # Get recent issues
    health_issues = cache.get('subscription_health_issues') or []
    
    return render_template(
        'admin/monitor.html',
        tasks=tasks,
        stats=stats,
        health_issues=health_issues
    ) 