"""Main application routes."""
from flask import Blueprint, render_template, send_file, jsonify
import os
import logging

logger = logging.getLogger(__name__)
main_bp = Blueprint('main', __name__)


@main_bp.route('/')
def home():
    """Render the home page."""
    try:
        return render_template('index.html')
    except Exception as e:
        logger.error(f"Error rendering home page: {e}")
        return render_template('base.html', error="Error loading home page")


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
