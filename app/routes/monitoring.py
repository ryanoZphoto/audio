"""Monitoring routes."""
import sys
import uuid
from flask import Blueprint, jsonify, current_app, request
from app.extensions import db, cache
from datetime import datetime
from app.utils.config_utils import get_secret

monitoring_bp = Blueprint('monitoring', __name__, url_prefix='/api/monitoring')

def generate_request_id():
    """Generate a unique request ID."""
    return str(uuid.uuid4())

@monitoring_bp.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    request_id = generate_request_id()
    db_url = get_secret('DATABASE_URL')
    redis_url = get_secret('REDIS_URL')
    
    return jsonify({
        'request_id': request_id,
        'status': 'healthy' if db_url and redis_url else 'unhealthy',
        'database': 'connected' if db_url else 'disconnected',
        'redis': 'connected' if redis_url else 'disconnected'
    })


def check_database():
    """Check database connection"""
    try:
        db.session.execute('SELECT 1')
        db.session.commit()
        return {'status': 'healthy'}
    except Exception as e:
        return {
            'status': 'unhealthy',
            'error': str(e)
        }


def check_redis():
    """Check Redis connection"""
    try:
        current_app.logger.info("Testing Redis connection...")
        cache.set('health_check', 'ok')
        result = cache.get('health_check')
        if result == 'ok':
            current_app.logger.info("Redis connection successful")
            return {'status': 'healthy'}
        else:
            current_app.logger.warning(
                "Redis connection failed: value mismatch"
            )
            return {
                'status': 'unhealthy',
                'error': 'Redis value mismatch'
            }
    except Exception as e:
        current_app.logger.error(
            f"Redis connection error: {str(e)}"
        )
        return {
            'status': 'unhealthy',
            'error': str(e)
        }


@monitoring_bp.route('/status', methods=['GET'])
def status():
    current_app.logger.info('Status endpoint called')
    try:
        # Log request details
        current_app.logger.info(f'Request headers: {dict(request.headers)}')
        current_app.logger.info(f'Request URL: {request.url}')
        
        # Try a simple database query to verify connection
        current_app.logger.info('Testing database connection...')
        db.session.execute('SELECT 1').scalar()
        db.session.commit()
        current_app.logger.info('Database connection successful')
        
        # Try a simple Redis operation to verify connection
        current_app.logger.info('Testing Redis connection...')
        cache.set('status_check', 'ok')
        cache_result = cache.get('status_check')
        current_app.logger.info(f'Redis connection result: {cache_result}')
        
        response_data = {
            'status': 'running',
            'message': 'Server is running',
            'timestamp': datetime.utcnow().isoformat(),
            'database': 'connected',
            'redis': 'connected' if cache_result == 'ok' else 'error',
            'debug_info': {
                'python_version': sys.version,
                'flask_env': get_secret('FLASK_ENV', 'production'),
                'request_id': get_secret('REQUEST_ID', get_secret('REQUEST_ID', ''))
            }
        }
        current_app.logger.info(f'Status response: {response_data}')
        return jsonify(response_data)
    except Exception as e:
        error_id = get_secret('REQUEST_ID', get_secret('REQUEST_ID', ''))
        current_app.logger.exception(
            f'Error in status endpoint (error_id: {error_id})'
        )
        return jsonify({
            'status': 'error',
            'message': str(e),
            'error_id': error_id,
            'timestamp': datetime.utcnow().isoformat()
        }), 500
