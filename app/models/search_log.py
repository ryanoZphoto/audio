"""Search log model."""
from datetime import datetime
from app.extensions import db


class SearchLog(db.Model):
    """Model for tracking search queries."""
    
    __tablename__ = 'search_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    query = db.Column(db.String(500), nullable=False)
    token = db.Column(db.String(100))
    ip_address = db.Column(db.String(45))
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    success = db.Column(db.Boolean, default=True)
    error = db.Column(db.String(500))
    
    def __repr__(self):
        """String representation."""
        return f'<SearchLog {self.query}>' 