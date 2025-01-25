from flask import request, jsonify
from app.models import IPTokenUsage
from datetime import datetime, timedelta

def get_remaining_tokens():
    ip_address = request.remote_addr
    ip_usage = IPTokenUsage.query.filter_by(ip_address=ip_address).first()
    
    if not ip_usage:
        # First time user
        ip_usage = IPTokenUsage(ip_address=ip_address)
        db.session.add(ip_usage)
        db.session.commit()
        return 3  # Full tokens for new IP
    
    # Check if it's been 24 hours since first use
    if datetime.utcnow() - ip_usage.first_used > timedelta(hours=24):
        # Reset the counter after 24 hours
        ip_usage.tokens_used = 0
        ip_usage.first_used = datetime.utcnow()
        db.session.commit()
        return 3
    
    return max(0, 3 - ip_usage.tokens_used)

@app.route('/search', methods=['POST'])
def search():
    remaining_tokens = get_remaining_tokens()
    
    if remaining_tokens <= 0:
        return jsonify({
            'error': 'No free tokens remaining. Please purchase a subscription.',
            'remaining_tokens': 0
        }), 403
    
    # Update token usage
    ip_address = request.remote_addr
    ip_usage = IPTokenUsage.query.filter_by(ip_address=ip_address).first()
    ip_usage.tokens_used += 1
    ip_usage.last_used = datetime.utcnow()
    db.session.commit()
    
    # ... rest of your search logic ... 