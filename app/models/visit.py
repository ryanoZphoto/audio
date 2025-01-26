"""Visit model for tracking site visits."""
from datetime import datetime
from app.extensions import db


class Visit(db.Model):
    """Model for tracking site visits."""
    
    __tablename__ = 'visits'
    
    id = db.Column(db.Integer, primary_key=True)
    ip_address = db.Column(db.String(45))
    user_agent = db.Column(db.String(255))
    path = db.Column(db.String(255))
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        """String representation."""
        return f'<Visit {self.path} at {self.timestamp}>' 