"""Admin blueprint routes."""
from flask import Blueprint, current_app
from app.utils.config_utils import get_secret

admin_bp = Blueprint('admin_panel', __name__)

def init_admin_config():
    """Initialize admin configuration."""
    admin_secret = get_secret('ADMIN_SECRET')
    if admin_secret:
        current_app.config['ADMIN_SECRET'] = admin_secret
