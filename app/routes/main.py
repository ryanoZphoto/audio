"""Main application routes."""
from flask import Blueprint, render_template, send_file, jsonify, send_from_directory, current_app
import os
import logging
from flask_sqlalchemy import SQLAlchemy
from flask_caching import Cache

logger = logging.getLogger(__name__)
main_bp = Blueprint('main', __name__)
db = SQLAlchemy()
cache = Cache()


@main_bp.route('/')
def index():
    """Render the main page."""
    ga4_id = os.getenv('GA4_ID')
    return render_template('index.html', ga4_id=ga4_id)


@main_bp.route('/favicon.ico')
def favicon():
    """Serve the favicon."""
    return send_from_directory(os.path.join(current_app.root_path, 'static'),
                             'favicon.ico', mimetype='image/vnd.microsoft.icon')


@main_bp.route('/static/<path:filename>')
def static_files(filename):
    """Serve static files."""
    return send_from_directory(
        os.path.join(current_app.root_path, '../static'),
        filename
    )


@main_bp.route('/clips/<path:filename>')
def download_file(filename):
    """Download a generated audio clip file."""
    try:
        file_path = os.path.join('clips', filename)
        if not os.path.exists(file_path):
            logger.error(f"File not found: {file_path}")
            return jsonify({"error": "File not found"}), 404
            
        return send_file(
            file_path,
            as_attachment=True
        )
    except Exception as e:
        logger.error(f"Error downloading file {filename}: {e}")
        return jsonify({"error": "Error downloading file"}), 500


@main_bp.route('/db-check')
def db_check():
    try:
        db.engine.connect()
        return "Database connection successful", 200
    except Exception as e:
        return f"Connection failed: {str(e)}", 500


@main_bp.route('/cache-test')
def cache_test():
    try:
        cache.set('test', 'works', timeout=30)
        return "Cache set successfully", 200
    except Exception as e:
        return f"Cache error: {str(e)}", 500


@main_bp.route('/cache-check')
def cache_check():
    value = cache.get('test')
    return f"Cache value: {value}", 200


@main_bp.route('/redis-check')
def redis_check():
    try:
        cache.set('test', 'works', timeout=10)
        return f"Redis value: {cache.get('test')}", 200
    except Exception as e:
        return f"Redis error: {str(e)}", 500


@main_bp.route('/health')
def health_check():
    return jsonify({"status": "healthy"}), 200
