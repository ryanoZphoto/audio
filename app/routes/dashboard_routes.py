from flask import Blueprint, render_template, jsonify, request
from datetime import datetime, timedelta
from sqlalchemy import func, extract
from app.extensions import db
from app.models import Visit, Subscription

dashboard_bp = Blueprint('dashboard', __name__)


@dashboard_bp.route('/')
def dashboard():
    """Render the dashboard page"""
    return render_template('admin/dashboard.html')


@dashboard_bp.route('/data')
def dashboard_data():
    """Get dashboard analytics data"""
    range_param = request.args.get('range', '24h')
    now = datetime.utcnow()
    
    # Calculate time ranges
    if range_param == '24h':
        start_time = now - timedelta(hours=24)
        time_group = extract('hour', Visit.timestamp)
    elif range_param == '7d':
        start_time = now - timedelta(days=7)
        time_group = extract('day', Visit.timestamp)
    else:  # 30d
        start_time = now - timedelta(days=30)
        time_group = extract('day', Visit.timestamp)

    # Visitor analytics
    visits_data = db.session.query(
        func.date_trunc('hour', Visit.timestamp).label('time_bucket'),
        func.count(Visit.id).label('visitors'),
        func.count(func.distinct(Visit.ip_address)).label('unique_visitors')
    ).filter(
        Visit.timestamp >= start_time
    ).group_by('time_bucket').all()

    # Sales data
    sales_data = db.session.query(
        func.date_trunc('hour', Subscription.created_at).label('time_bucket'),
        func.count(Subscription.id).label('sales')
    ).filter(
        Subscription.created_at >= start_time
    ).group_by('time_bucket').all()

    # Format response
    labels = [bucket[0].strftime('%Y-%m-%d %H:%M') for bucket in visits_data]
    visitors = [bucket[1] for bucket in visits_data]
    purchases = [0] * len(labels)  # Initialize with zeros
    
    for sale in sales_data:
        sale_time = sale[0].strftime('%Y-%m-%d %H:%M')
        if sale_time in labels:
            idx = labels.index(sale_time)
            purchases[idx] = sale[1]

    # Get top pages
    top_pages = db.session.query(
        Visit.path,
        func.count(Visit.id).label('views')
    ).filter(
        Visit.timestamp >= start_time
    ).group_by(Visit.path).order_by(
        func.count(Visit.id).desc()
    ).limit(5).all()

    return jsonify({
        'labels': labels,
        'visitors': visitors,
        'purchases': purchases,
        'top_pages': [
            {'path': path, 'views': views} 
            for path, views in top_pages
        ]
    })
