"""Payment log model for tracking payment events."""

from datetime import datetime
from app.extensions import db


class PaymentLog(db.Model):
    """Model for tracking payment events."""

    __tablename__ = 'payment_logs'

    id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.Integer, db.ForeignKey('customers.id'), nullable=False)
    subscription_id = db.Column(db.Integer, db.ForeignKey('subscriptions.id'), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    currency = db.Column(db.String(3), nullable=False)
    status = db.Column(db.String(20), nullable=False)
    payment_method = db.Column(db.String(50), nullable=False)
    stripe_payment_id = db.Column(db.String(100), unique=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    customer = db.relationship('Customer', backref=db.backref('payment_logs', lazy=True))
    subscription = db.relationship('Subscription', backref=db.backref('payment_logs', lazy=True))

    def __repr__(self):
        """Return string representation."""
        return f'<PaymentLog {self.id} - {self.status}>' 