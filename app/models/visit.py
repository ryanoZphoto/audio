"""Website visit tracking model."""
from datetime import datetime
from app.extensions import db

class Visit(db.Model):
    __tablename__ = 'visits'
    
    id = db.Column(db.Integer, primary_key=True)
    ip_address = db.Column(db.String(45))
    user_agent = db.Column(db.Text)
    path = db.Column(db.String(500))
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    subscription_id = db.Column(db.Integer, db.ForeignKey('subscriptions.id')) 