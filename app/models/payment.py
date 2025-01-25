"""Payment model."""
from datetime import datetime
from app.extensions import db

class PaymentLog(db.Model):
    __tablename__ = 'payment_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    amount = db.Column(db.Float, nullable=False)
    currency = db.Column(db.String(3), default='USD')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    subscription_id = db.Column(db.Integer, db.ForeignKey('subscriptions.id')) 