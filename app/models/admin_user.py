"""Admin user model."""

from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from app.extensions import db


class AdminUser(UserMixin, db.Model):
    """Model for admin users."""

    __tablename__ = 'admin_users'

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime)

    def set_password(self, password):
        """Set password hash."""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        """Check password hash."""
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        """Return string representation."""
        return f'<AdminUser {self.email}>' 