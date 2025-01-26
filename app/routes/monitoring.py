"""Monitoring routes."""
import os
import sys
import uuid
import psutil
import logging
from flask import Blueprint, jsonify, current_app, request
from app.extensions import db, cache
from datetime import datetime

monitoring_bp = Blueprint('monitoring', __name__, url_prefix='/api/monitoring')
logger = logging.getLogger(__name__)


def generate_request_id():
    """Generate a unique request ID."""
    return str(uuid.uuid4())


@monitoring_bp.route('/health', methods=['GET'])
def health_check():
    """Basic health check endpoint."""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.utcnow().isoformat(),
        'environment': os.getenv('FLASK_ENV', 'production'),
        'request_id': os.getenv('REQUEST_ID', '')
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
    """Get application status."""
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
                'flask_env': os.getenv('FLASK_ENV', 'production'),
                'request_id': os.getenv('REQUEST_ID', '')
            }
        }
        current_app.logger.info(f'Status response: {response_data}')
        return jsonify(response_data)
    except Exception as e:
        error_id = os.getenv('REQUEST_ID', '')
        current_app.logger.exception(
            f'Error in status endpoint (error_id: {error_id})'
        )
        return jsonify({
            'status': 'error',
            'message': str(e),
            'error_id': error_id,
            'timestamp': datetime.utcnow().isoformat()
        }), 500


@monitoring_bp.route('/system', methods=['GET'])
def system_info():
    """Get system resource usage."""
    try:
        cpu_percent = psutil.cpu_percent()
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        return jsonify({
            'success': True,
            'cpu': {
                'percent': cpu_percent
            },
            'memory': {
                'total': memory.total,
                'available': memory.available,
                'percent': memory.percent
            },
            'disk': {
                'total': disk.total,
                'used': disk.used,
                'free': disk.free,
                'percent': disk.percent
            }
        })
    except Exception as e:
        logger.error(f"Error getting system info: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@monitoring_bp.route('/error', methods=['GET'])
def error_info():
    """Get error information."""
    try:
        error_id = os.getenv('REQUEST_ID', '')
        return jsonify({
            'success': True,
            'error_id': error_id
        })
    except Exception as e:
        logger.error(f"Error getting error info: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
