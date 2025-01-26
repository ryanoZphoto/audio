from flask import Blueprint, request, jsonify, send_file, current_app
import os
import logging
from transformers import pipeline
import torch
from app.extensions import cache
from app.utils.youtube_search_and_clip import (
    setup_youtube_api, get_video_transcript,
    search_word_in_transcript, download_audio_clip
)
from app.services.search_manager import SearchManager
from datetime import datetime


logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


search_bp = Blueprint('search', __name__)

# Initialize YouTube API client
youtube = setup_youtube_api()


def get_ai_model():
    """Get AI model configuration."""
    return current_app.config.get(
        'AI_MODEL_VERSION',
        'distilbert-base-uncased-distilled-squad'
    )


def get_qa_pipeline():
    """Initialize question-answering pipeline."""
    return pipeline(
        "question-answering",
        model=get_ai_model(),
        device_map="auto",
        torch_dtype=(
            torch.float16 if torch.cuda.is_available() else torch.float32
        )
    )


@search_bp.route('/search', methods=['POST'])
def search():
    """Handle search requests."""
    try:
        data = request.get_json()
        if not data:
            logger.error("No JSON data provided in request")
            return jsonify({'error': 'No JSON data provided'}), 400

        # Log request data for debugging
        logger.debug(f"Search request data: {data}")
        
        # Validate required fields
        required_fields = ['query', 'token']
        missing_fields = [field for field in required_fields if field not in data]
        if missing_fields:
            logger.error(f"Missing required fields: {missing_fields}")
            return jsonify({'error': f'Missing required fields: {missing_fields}'}), 400

        # Initialize search manager
        search_mgr = SearchManager()
        
        # Validate token and check search limits
        token = data.get('token')
        if not search_mgr.validate_token(token):
            logger.error(f"Invalid token provided: {token}")
            return jsonify({'error': 'Invalid token'}), 401

        # Get search parameters
        query = data.get('query')
        channel_id = data.get('channel_id')

        try:
            # Perform YouTube search
            search_results = youtube.search().list(
                part="id,snippet",
                q=query,
                type="video",
                channelId=channel_id if channel_id else None,
                maxResults=10
            ).execute()

            # Process and return results
            videos = []
            for item in search_results.get('items', []):
                video_id = item['id']['videoId']
                transcript = get_video_transcript(video_id)
                matches = []
                
                if transcript:
                    matches = search_word_in_transcript(transcript, data.get('query', ''))
                
                if matches:
                    videos.append({
                        'id': video_id,
                        'title': item['snippet']['title'],
                        'description': item['snippet']['description'],
                        'thumbnail': item['snippet']['thumbnails']['default']['url'],
                        'matches': matches
                    })

            logger.info(f"Successfully found {len(videos)} videos with matches for query: {query}")
            return jsonify({
                'success': True,
                'results': videos  # Changed from 'videos' to 'results' to match frontend
            })

        except Exception as e:
            logger.error(f"YouTube API error: {str(e)}")
            return jsonify({
                'error': 'Error searching YouTube videos',
                'details': str(e)
            }), 500

    except Exception as e:
        logger.error(f"Unexpected error in search route: {str(e)}")
        return jsonify({
            'error': 'Internal server error',
            'details': str(e)
        }), 500


@search_bp.route('/download_clip', methods=['POST'])
def download_clip():
    """Download an audio clip from a YouTube video."""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
            
        video_id = data.get('video_id')
        if not video_id:
            return jsonify({'error': 'video_id is required'}), 400
            
        video_url = f"https://youtube.com/watch?v={video_id}"
        start_time = float(data.get('timestamp', 0))
        duration = float(data.get('duration', 1.0))
        
        output_file = download_audio_clip(
            video_url,
            start_time,
            duration
        )
        
        if output_file:
            return jsonify({
                'success': True,
                'file_path': output_file
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Failed to create clip'
            })
            
    except Exception as e:
        logger.exception("Error in download_clip endpoint")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@search_bp.route('/clips/<path:filename>')
def download_file(filename):
    """Download a generated audio clip."""
    try:
        return send_file(
            os.path.join('clips', filename),
            as_attachment=True
        )
    except Exception as e:
        logger.exception("Error downloading clip")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@search_bp.route('/check_searches', methods=['POST'])
def check_searches():
    """Check remaining searches for a token or free tier."""
    try:
        data = request.get_json()
        token = data.get('access_token', '').strip() if data else ''
        client_ip = request.headers.get('X-Forwarded-For', request.remote_addr)
        
        search_mgr = SearchManager()
        
        if token:
            status = search_mgr.check_subscription(token)
            if status['valid']:
                return jsonify({
                    'success': True,
                    'searches_remaining': status['remaining'],
                    'searches_used': status['used'],
                    'expires': status['expires'].isoformat() if isinstance(status['expires'], datetime) else status['expires']
                })
        
        # Return free tier status
        usage = search_mgr.get_free_searches(client_ip)
        return jsonify({
            'success': True,
            'searches_remaining': usage['remaining'],
            'searches_used': usage['used'],
            'expires': usage['expires']  # Already in ISO format from SearchManager
        })
        
    except Exception as e:
        logger.error(f"Error checking searches: {e}", exc_info=True)
        return jsonify({
            'error': 'Internal server error',
            'details': str(e)
        }), 500
