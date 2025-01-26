"""
Routes package for AudioSnipt application.
Contains all route blueprints for different sections of the application.
"""

from flask import Blueprint

# Create blueprints with url_prefix
search_bp = Blueprint('search', __name__, url_prefix='/api/search')
blog_bp = Blueprint('blog', __name__, url_prefix='/blog')
seo_bp = Blueprint('seo', __name__, url_prefix='/seo')
monitoring_bp = Blueprint('monitoring', __name__, url_prefix='/api/monitoring')
main_bp = Blueprint('main', __name__, url_prefix='/')
payment_bp = Blueprint('payment', __name__, url_prefix='/api/payment')
dashboard_bp = Blueprint('dashboard', __name__, url_prefix='/dashboard')

# Import views to register routes
from .monitoring import *  # noqa
from .search import *  # noqa
from .blog import *  # noqa
from .payment_routes import *  # noqa
from .dashboard_routes import *  # noqa
from .main import *  # noqa

# Export blueprints
__all__ = [
    'search_bp',
    'blog_bp',
    'seo_bp',
    'monitoring_bp',
    'main_bp',
    'payment_bp',
    'dashboard_bp'
]
