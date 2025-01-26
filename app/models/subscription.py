"""Subscription model."""
from datetime import datetime
from app.extensions import db


class Subscription(db.Model):
    """Model for user subscriptions."""
    
    __tablename__ = 'subscriptions'
    
    id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.Integer, db.ForeignKey('customers.id'), nullable=False)
    plan_type = db.Column(db.String(20))  # Allow NULL for testing invalid subscriptions
    status = db.Column(db.String(20), nullable=False)
    search_limit = db.Column(db.Integer, nullable=False)
    start_date = db.Column(db.DateTime, default=datetime.utcnow)
    expiry_date = db.Column(db.DateTime)
    access_token = db.Column(db.String(100), unique=True)
    is_recurring = db.Column(db.Boolean, default=False)
    stripe_subscription_id = db.Column(db.String(100), unique=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )
    
    def __repr__(self):
        """Return string representation."""
        return f'<Subscription {self.plan_type} - {self.status}>' 