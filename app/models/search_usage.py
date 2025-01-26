"""Search usage model."""
from datetime import datetime
from app.extensions import db


class SearchUsage(db.Model):
    """Model for tracking search usage."""
    
    __tablename__ = 'search_usage'
    
    id = db.Column(db.Integer, primary_key=True)
    token = db.Column(db.String(100), nullable=False)
    ip_address = db.Column(db.String(45))
    count = db.Column(db.Integer, default=0)
    last_search = db.Column(db.DateTime, default=datetime.utcnow)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        """String representation."""
        return f'<SearchUsage {self.token}: {self.count}>' 