"""Main application routes."""
from flask import Blueprint, render_template, request, send_file, jsonify
import os
import logging

logger = logging.getLogger(__name__)
main_bp = Blueprint('main', __name__)


@main_bp.route('/')
def home():
    return "Welcome to AudioSnipt!"


@main_bp.route('/clips/<path:filename>')
def download_file(filename):
    """Download a generated audio clip file."""
    return send_file(
        os.path.join('clips', filename),
        as_attachment=True
    ) 