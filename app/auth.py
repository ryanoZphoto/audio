from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from datetime import datetime, timedelta
from app.models import AdminUser
from app.extensions import db
import logging
import os
import jwt
from functools import wraps

auth_bp = Blueprint('auth', __name__)
login_manager = LoginManager()
logger = logging.getLogger(__name__)


@login_manager.user_loader
def load_user(user_id):
    """Load user by ID"""
    return AdminUser.query.get(int(user_id))


@login_manager.unauthorized_handler
def unauthorized():
    """Handle unauthorized access attempts"""
    flash('You must be logged in to access this page.', 'danger')
    return redirect(url_for('auth.login', next=request.url))


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Handle admin login"""
    if current_user.is_authenticated:
        return redirect(url_for('admin.dashboard'))
    
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        remember = request.form.get('remember', False)
        
        user = AdminUser.query.filter_by(email=email).first()
        
        if user and user.check_password(password):
            login_user(user, remember=remember)
            user.last_login = datetime.now()
            db.session.commit()
            
            next_page = request.args.get('next')
            if next_page:
                return redirect(next_page)
            return redirect(url_for('admin.dashboard'))
        
        flash('Invalid email or password', 'danger')
    
    return render_template('admin/login.html')


@auth_bp.route('/change-password', methods=['GET', 'POST'])
@login_required
def change_password():
    """Handle password change"""
    if request.method == 'POST':
        current_password = request.form.get('current_password')
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')
        
        if not current_user.check_password(current_password):
            flash('Current password is incorrect', 'danger')
            return redirect(url_for('auth.change_password'))
        
        if new_password != confirm_password:
            flash('New password and confirmation do not match', 'danger')
            return redirect(url_for('auth.change_password'))
        
        if len(new_password) < 8:
            flash('Password must be at least 8 characters long', 'danger')
            return redirect(url_for('auth.change_password'))
        
        current_user.set_password(new_password)
        db.session.commit()
        
        flash('Password changed successfully', 'success')
        return redirect(url_for('admin.dashboard'))
    
    return render_template('admin/change_password.html')


@auth_bp.route('/logout')
@login_required
def logout():
    """Handle admin logout"""
    logout_user()
    flash('You have been logged out.', 'success')
    return redirect(url_for('auth.login'))


def generate_token(user_id, expiry=None):
    """Generate a JWT token for a user."""
    if expiry is None:
        expiry = datetime.utcnow() + timedelta(days=1)
    
    token_secret = os.getenv('TOKEN_SECRET')
    if not token_secret:
        raise ValueError("TOKEN_SECRET not configured")
        
    payload = {
        'user_id': user_id,
        'exp': expiry
    }
    return jwt.encode(payload, token_secret, algorithm='HS256')

def verify_token(token):
    """Verify a JWT token."""
    try:
        token_secret = os.getenv('TOKEN_SECRET')
        if not token_secret:
            raise ValueError("TOKEN_SECRET not configured")
            
        payload = jwt.decode(token, token_secret, algorithms=['HS256'])
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None