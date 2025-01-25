from datetime import datetime
from app.extensions import db
from sqlalchemy.sql import func
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin


class AdminUser(UserMixin, db.Model):
    """Admin user model for authentication"""
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=func.now())
    last_login = db.Column(db.DateTime)

    def set_password(self, password):
        """Set the password hash"""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        """Check if password matches"""
        return check_password_hash(self.password_hash, password)


class Customer(db.Model):
    """Customer model for storing user information"""
    id = db.Column(db.Integer, primary_key=True)
    stripe_customer_id = db.Column(
        db.String(100), unique=True, nullable=False
    )
    email = db.Column(db.String(120), unique=True)
    created_at = db.Column(db.DateTime, default=func.now())
    subscriptions = db.relationship(
        'Subscription', backref='customer', lazy=True
    )


class Subscription(db.Model):
    """Subscription model for storing subscription information"""
    id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(
        db.Integer, db.ForeignKey('customer.id'), nullable=False
    )
    stripe_subscription_id = db.Column(
        db.String(100), unique=True
    )
    plan_type = db.Column(db.String(50), nullable=False)
    status = db.Column(
        db.String(20), nullable=False
    )  # active, expired, cancelled
    search_limit = db.Column(db.Integer, nullable=False)
    searches_used = db.Column(db.Integer, default=0)
    start_date = db.Column(
        db.DateTime, nullable=False, default=func.now()
    )
    expiry_date = db.Column(db.DateTime, nullable=False)
    is_recurring = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=func.now())
    updated_at = db.Column(
        db.DateTime, default=func.now(), onupdate=func.now()
    )


class SearchLog(db.Model):
    """Model for tracking search usage"""
    id = db.Column(db.Integer, primary_key=True)
    subscription_id = db.Column(
        db.Integer, 
        db.ForeignKey('subscription.id'), 
        nullable=False
    )
    search_query = db.Column(db.String(500), nullable=False)
    timestamp = db.Column(db.DateTime, default=func.now())
    success = db.Column(db.Boolean, default=True)


class PaymentLog(db.Model):
    """Model for tracking payment events"""
    id = db.Column(db.Integer, primary_key=True)
    stripe_event_id = db.Column(
        db.String(100), unique=True, nullable=False
    )
    customer_id = db.Column(db.Integer, db.ForeignKey('customer.id'))
    event_type = db.Column(db.String(50), nullable=False)
    amount = db.Column(db.Integer)
    status = db.Column(db.String(20))
    error_message = db.Column(db.String(500))
    created_at = db.Column(db.DateTime, default=func.now())


class SearchUsage(db.Model):
    """Model for tracking search usage by token."""
    id = db.Column(db.Integer, primary_key=True)
    token = db.Column(db.String(255), unique=True, nullable=False)
    searches_used = db.Column(db.Integer, default=0)
    searches_remaining = db.Column(db.Integer, nullable=False)
    expiry_date = db.Column(db.DateTime, nullable=False)
    created_at = db.Column(
        db.DateTime, nullable=False, default=datetime.utcnow
    )
    last_search_at = db.Column(db.DateTime)

    def is_valid(self):
        """Check if the token is valid and has searches remaining."""
        now = datetime.utcnow()
        return (
            self.searches_remaining > 0 and 
            self.expiry_date > now
        )


class Visit(db.Model):
    """Model for tracking page visits and analytics."""
    id = db.Column(db.Integer, primary_key=True)
    ip_address = db.Column(db.String(45), nullable=False)  # IPv6 support
    path = db.Column(db.String(500), nullable=False)
    user_agent = db.Column(db.String(500))
    referer = db.Column(db.String(500))
    timestamp = db.Column(
        db.DateTime, nullable=False, default=datetime.utcnow
    )
    session_id = db.Column(db.String(100))
    duration = db.Column(db.Integer)  # Duration in seconds
