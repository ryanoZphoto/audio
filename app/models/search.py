"""Search model."""
from datetime import datetime
from app.extensions import db

class SearchLog(db.Model):
    __tablename__ = 'search_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    search_query = db.Column(db.String(500), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    success = db.Column(db.Boolean, default=True)
    subscription_id = db.Column(db.Integer, db.ForeignKey('subscriptions.id')) 