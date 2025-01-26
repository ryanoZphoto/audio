import os
import logging
import psutil
import requests
from datetime import datetime, timedelta
from flask import render_template, jsonify, request, current_app
from flask_login import login_required, current_user
from flask_admin import Admin
from flask_admin.contrib.sqla import ModelView
from app.admin_bp import admin_bp
from app.models import Customer, Subscription, SearchLog, PaymentLog, AdminUser, SearchUsage
from app.utils.subscription_utils import get_subscription_stats
from app.extensions import db

logger = logging.getLogger(__name__)


def init_admin(app):
    """Initialize Flask-Admin."""
    admin = Admin(app, name='Admin Dashboard', template_mode='bootstrap4')
    
    # Secure admin views
    class SecureModelView(ModelView):
        def is_accessible(self):
            admin_secret = os.getenv('ADMIN_SECRET')
            if not admin_secret:
                logger.warning("ADMIN_SECRET not configured")
                return False
                
            auth_header = request.headers.get('Authorization')
            if not auth_header:
                return False
                
            try:
                scheme, token = auth_header.split()
                if scheme.lower() != 'bearer':
                    return False
                return token == admin_secret
            except:
                return False
    
    # Add model views
    admin.add_view(SecureModelView(AdminUser, db.session))
    admin.add_view(SecureModelView(SearchUsage, db.session))
    admin.add_view(SecureModelView(SearchLog, db.session))
    admin.add_view(SecureModelView(Subscription, db.session))
    
    logger.info("Admin interface initialized")


logger = logging.getLogger(__name__)


def check_youtube_api():
    """Check if YouTube API is accessible"""
    try:
        # Try to fetch a test video's info
        test_video_id = 'dQw4w9WgXcQ'  # Known video ID
        url = (
            f'https://www.googleapis.com/youtube/v3/videos'
            f'?id={test_video_id}'
            f'&key={current_app.config["YOUTUBE_API_KEY"]}'
            f'&part=snippet'
        )
        response = requests.get(url, timeout=5)
        return response.status_code == 200
    except Exception as e:
        logger.error(f"YouTube API check failed: {str(e)}")
        return False


def check_stripe_api():
    """Check if Stripe API is accessible"""
    try:
        import stripe
        stripe.api_key = current_app.config['STRIPE_SECRET_KEY']
        # Try to list a single customer (lightweight operation)
        stripe.Customer.list(limit=1)
        return True
    except Exception as e:
        logger.error(f"Stripe API check failed: {str(e)}")
        return False


def get_system_stats():
    """Get system resource usage stats"""
    cpu_percent = psutil.cpu_percent()
    memory = psutil.virtual_memory()
    disk = psutil.disk_usage('/')
    
    # Calculate clips folder size
    clips_folder_size = 0
    clips_path = os.path.join(current_app.root_path, 'static', 'clips')
    if os.path.exists(clips_path):
        for path, dirs, files in os.walk(clips_path):
            for f in files:
                fp = os.path.join(path, f)
                clips_folder_size += os.path.getsize(fp)
    
    # Convert to MB
    clips_folder_size = clips_folder_size / (1024 * 1024)
    
    return {
        'cpu_percent': cpu_percent,
        'memory_percent': memory.percent,
        'disk_percent': disk.percent,
        'clips_folder_size': clips_folder_size
    }


@admin_bp.route('/dashboard')
@login_required
def dashboard():
    """Admin dashboard showing subscription overview"""
    # Get active subscriptions
    active_subs = Subscription.query.filter_by(status='active').all()
    
    # Get recent payments
    recent_payments = PaymentLog.query.order_by(
        PaymentLog.created_at.desc()
    ).limit(10).all()
    
    # Get search activity
    recent_searches = SearchLog.query.order_by(
        SearchLog.timestamp.desc()
    ).limit(20).all()
    
    return render_template(
        'admin/dashboard.html',
        active_subs=active_subs,
        recent_payments=recent_payments,
        recent_searches=recent_searches
    )


@admin_bp.route('/subscriptions')
@login_required
def subscriptions():
    """List all subscriptions"""
    subscriptions = Subscription.query.all()
    return render_template(
        'admin/subscriptions.html',
        subscriptions=subscriptions
    )


@admin_bp.route('/subscription/<int:sub_id>')
@login_required
def subscription_detail(sub_id):
    """Show detailed subscription information"""
    subscription = Subscription.query.get_or_404(sub_id)
    stats = get_subscription_stats(sub_id)
    
    # Get search history
    searches = SearchLog.query.filter_by(
        subscription_id=sub_id
    ).order_by(SearchLog.timestamp.desc()).all()
    
    return render_template(
        'admin/subscription_detail.html',
        subscription=subscription,
        stats=stats,
        searches=searches
    )


@admin_bp.route('/customers')
@login_required
def customers():
    """List all customers"""
    customers = Customer.query.all()
    return render_template('admin/customers.html', customers=customers)


@admin_bp.route('/reports')
@login_required
def reports():
    """Generate subscription reports"""
    # Get date range from query params
    days = int(request.args.get('days', 30))
    start_date = datetime.now() - timedelta(days=days)
    
    # Get subscription stats
    new_subs = Subscription.query.filter(
        Subscription.created_at >= start_date
    ).count()
    
    expired_subs = Subscription.query.filter(
        Subscription.status == 'expired',
        Subscription.updated_at >= start_date
    ).count()
    
    total_searches = SearchLog.query.filter(
        SearchLog.timestamp >= start_date
    ).count()
    
    return jsonify({
        'new_subscriptions': new_subs,
        'expired_subscriptions': expired_subs,
        'total_searches': total_searches,
        'period_days': days
    })


@admin_bp.route('/troubleshoot')
@login_required
def troubleshoot():
    """Show system troubleshooting information"""
    # Get system status
    system_stats = get_system_stats()
    
    # Check external services
    youtube_status = check_youtube_api()
    stripe_status = check_stripe_api()
    
    # Get recent errors from log
    recent_errors = []
    try:
        with open('search_debug.log', 'r') as f:
            lines = f.readlines()
            for line in reversed(lines[-100:]):  # Check last 100 lines
                if 'ERROR' in line:
                    recent_errors.append(line.strip())
                if len(recent_errors) >= 5:  # Get last 5 errors
                    break
    except Exception as e:
        logger.error(f"Error reading log file: {str(e)}")
    
    # Common issues and solutions
    common_issues = [
        {
            'symptom': 'Search not finding known phrases',
            'possible_causes': [
                'Video lacks proper transcripts',
                'Phrase might be spelled differently',
                'Video is too recent (transcripts not yet available)'
            ],
            'solutions': [
                'Check if video has closed captions',
                'Try alternative spellings or phrasings',
                'Wait a few hours for new videos'
            ]
        },
        {
            'symptom': 'Audio clips not downloading',
            'possible_causes': [
                'FFmpeg not installed or misconfigured',
                'Disk space full',
                'Video unavailable or restricted'
            ],
            'solutions': [
                'Check FFmpeg installation',
                'Clear clips directory',
                'Verify video accessibility'
            ]
        },
        {
            'symptom': 'Payment processing issues',
            'possible_causes': [
                'Stripe API key invalid',
                'Webhook misconfiguration',
                'Network connectivity issues'
            ],
            'solutions': [
                'Verify Stripe API keys',
                'Check webhook endpoints',
                'Test network connectivity'
            ]
        }
    ]
    
    return render_template(
        'admin/troubleshoot.html',
        system_stats=system_stats,
        youtube_status=youtube_status,
        stripe_status=stripe_status,
        recent_errors=recent_errors,
        common_issues=common_issues
    )


@admin_bp.route('/system-health')
@login_required
def system_health():
    """Get current system health metrics"""
    return jsonify({
        'stats': get_system_stats(),
        'services': {
            'youtube_api': check_youtube_api(),
            'stripe_api': check_stripe_api()
        }
    })


@admin_bp.route('/clear-clips', methods=['POST'])
@login_required
def clear_clips():
    """Clear all stored audio clips"""
    try:
        clips_path = os.path.join(current_app.root_path, 'static', 'clips')
        if os.path.exists(clips_path):
            for file in os.listdir(clips_path):
                file_path = os.path.join(clips_path, file)
                try:
                    if os.path.isfile(file_path):
                        os.unlink(file_path)
                except Exception as e:
                    logger.error(f"Error deleting {file_path}: {str(e)}")
        return jsonify({'success': True})
    except Exception as e:
        logger.error(f"Error clearing clips: {str(e)}")
        return jsonify({'success': False, 'error': str(e)})


@admin_bp.route('/reset-admin', methods=['POST'])
def reset_admin():
    """Reset admin user credentials"""
    try:
        # Only allow this in development/testing
        if current_app.config['ENV'] != 'production':
            admin = AdminUser.query.filter_by(
                email='admin@audiosnipt.com'
            ).first()
            if not admin:
                admin = AdminUser(email='admin@audiosnipt.com')
                db.session.add(admin)
            
            # Set a new password
            new_password = 'AudioSnipt2024!'
            admin.set_password(new_password)
            db.session.commit()
            
            return jsonify({
                'success': True,
                'message': (
                    'Admin user reset. '
                    f'Email: admin@audiosnipt.com, '
                    f'Password: {new_password}'
                )
            })
        else:
            return jsonify({
                'success': False,
                'message': 'This operation is not allowed in production'
            }), 403
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500
