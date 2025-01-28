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
    logger.info("Received search request")
    try:
        data = request.get_json()
        if not data:
            logger.error("No JSON data provided in request")
            return jsonify({'error': 'No JSON data provided'}), 400

        # Log request data for debugging
        logger.debug(f"Search request data: {data}")
        
        # Get client IP for free tier tracking
        client_ip = request.headers.get('X-Forwarded-For', request.remote_addr)
        
        # Initialize search manager
        search_mgr = SearchManager()
        
        # Check token if provided
        token = data.get('token', '').strip()
        if token:
            logger.info("Token provided - checking subscription")
            status = search_mgr.check_subscription(token)
            if not status['valid']:
                logger.error(f"Invalid token: {status.get('error', 'Unknown error')}")
                return jsonify({'error': status.get('error', 'Invalid token')}), 401
            if status['remaining'] <= 0:
                return jsonify({'error': 'Search limit reached'}), 403
        else:
            logger.info("No token provided - checking free searches")
            # Use SearchManager's safe cache operations for free tier
            if not search_mgr.increment_free_usage(client_ip):
                return jsonify({'error': 'Free search limit reached'}), 403

        # Get search parameters
        person_name = data.get('person_name')
        search_word = data.get('search_word')
        if not person_name or not search_word:
            logger.error("Missing required search parameters")
            return jsonify({'error': 'Missing person_name or search_word'}), 400

        try:
            # Perform YouTube search
            search_query = f"{person_name} {search_word}"
            logger.info(f"Performing YouTube search for: {search_query}")
            
            search_results = youtube.search().list(
                part="id,snippet",
                q=search_query,
                type="video",
                maxResults=10
            ).execute()

            # Process results
            videos = []
            for item in search_results.get('items', []):
                try:
                    video_id = item['id']['videoId']
                    transcript = get_video_transcript(video_id)
                    
                    if transcript:
                        matches = search_word_in_transcript(transcript, search_word)
                        if matches:
                            videos.append({
                                'id': video_id,
                                'title': item['snippet']['title'],
                                'description': item['snippet']['description'],
                                'thumbnail': item['snippet']['thumbnails']['default']['url'],
                                'matches': matches
                            })
                except Exception as video_error:
                    logger.error(f"Error processing video {video_id}: {str(video_error)}")
                    continue

            # Update usage if using subscription
            if token and status['valid']:
                search_mgr.increment_subscription_usage(token)

            logger.info(f"Found {len(videos)} videos with matches")
            return jsonify({
                'success': True,
                'results': videos
            })

        except Exception as youtube_error:
            logger.error(f"YouTube API error: {str(youtube_error)}")
            return jsonify({
                'error': 'Error searching YouTube videos',
                'details': str(youtube_error)
            }), 500

    except Exception as e:
        logger.error(f"Unexpected error in search route: {str(e)}", exc_info=True)
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
        token = data.get('token', '').strip() if data else ''
        client_ip = request.headers.get('X-Forwarded-For', request.remote_addr)
        
        search_mgr = SearchManager()
        
        if token:
            status = search_mgr.check_subscription(token)
            if status['valid']:
                return jsonify({
                    'success': True,
                    'searches_remaining': status['remaining'],
                    'searches_used': status['used'],
                    'expires': status['expires']
                })
        
        # Return free tier status
        usage = search_mgr.get_free_searches(client_ip)
        return jsonify({
            'success': True,
            'searches_remaining': usage['remaining'],
            'searches_used': usage['used'],
            'expires': usage['expires']
        })
        
    except Exception as e:
        logger.error(f"Error checking searches: {e}", exc_info=True)
        return jsonify({
            'error': 'Internal server error',
            'details': str(e)
        }), 500
