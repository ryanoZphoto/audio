"""Customer model."""
from datetime import datetime
from app.extensions import db


class Customer(db.Model):
    """Model for storing customer information."""
    
    __tablename__ = 'customers'
    
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    name = db.Column(db.String(100))
    stripe_customer_id = db.Column(db.String(100), unique=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    subscriptions = db.relationship('Subscription', backref='customer', lazy=True)
    
    def __repr__(self):
        """String representation."""
        return f'<Customer {self.email}>' 