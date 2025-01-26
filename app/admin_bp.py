"""Admin blueprint routes."""
import os
from flask import Blueprint, request, jsonify
from functools import wraps

admin_bp = Blueprint('admin', __name__)

def admin_required(f):
    """Decorator to require admin authentication."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        admin_secret = os.getenv('ADMIN_SECRET')
        if not admin_secret:
            return jsonify({
                'error': 'Admin authentication not configured'
            }), 500
            
        auth_header = request.headers.get('Authorization')
        if not auth_header:
            return jsonify({'error': 'No authorization header'}), 401
            
        try:
            scheme, token = auth_header.split()
            if scheme.lower() != 'bearer':
                return jsonify({
                    'error': 'Invalid authorization scheme'
                }), 401
                
            if token != admin_secret:
                return jsonify({'error': 'Invalid admin token'}), 401
                
            return f(*args, **kwargs)
        except ValueError:
            return jsonify({
                'error': 'Invalid authorization header format'
            }), 401
            
    return decorated_function
