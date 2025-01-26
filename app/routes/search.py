from flask import Blueprint, request, jsonify, send_file
import os
from datetime import datetime, timedelta
import hmac
import hashlib
from app.extensions import db
from app.models import SearchLog
from app.utils.youtube_search_and_clip import (
    setup_youtube_api, search_videos, get_video_transcript,
    search_word_in_transcript, format_timestamp, download_audio_clip
)
import logging
from flask_caching import Cache
from transformers import pipeline
import torch
from flask import current_app

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)  # Set to DEBUG level

search_bp = Blueprint('search', __name__)
cache = None

# Defer configuration access until request time
def get_ai_model():
    return current_app.config['AI_MODEL_VERSION']

def get_qa_pipeline():
    return pipeline(
        "question-answering",
        model=get_ai_model(),
        device_map="auto",
        torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32
    )

def init_search_bp(app_cache):
    """Initialize the search blueprint with cache instance"""
    global cache
    cache = app_cache
    logger.info("Search blueprint initialized with cache")

@search_bp.route('/search', methods=['POST'])
def search():
    """Search for phrases in YouTube videos with AI enhancement."""
    logger.info("Received search request")
    data = request.get_json()
    
    # Log request data (excluding sensitive info)
    logger.debug(f"Search request data: person_name={data.get('person_name')}, search_word={data.get('search_word')}")
    
    access_token = data.get('access_token')
    client_ip = request.headers.get('X-Forwarded-For', request.remote_addr)
    
    if access_token:
        logger.info(f"Processing access token: {access_token[:10]}...")
        try:
            # Split token and validate format
            parts = access_token.split(':')
            if len(parts) != 4:
                logger.error(f"Invalid token format - expected 4 parts, got {len(parts)}")
                return jsonify({'error': 'Invalid token format'}), 400
                
            plan_type, expiry_date, search_limit, signature = parts
            logger.debug(f"Token parts - plan: {plan_type}, expires: {expiry_date}, limit: {search_limit}")
            
            # Verify signature
            message = f"{plan_type}:{expiry_date}:{search_limit}"
            secret_key = os.getenv('TOKEN_SECRET', 'your-secret-key')
            expected_signature = hmac.new(
                secret_key.encode(),
                message.encode(),
                hashlib.sha256
            ).hexdigest()
            
            if signature != expected_signature:
                logger.error("Token signature verification failed")
                return jsonify({'error': 'Invalid token signature'}), 400
            
            # Check expiry
            expiry = datetime.fromisoformat(expiry_date)
            if expiry < datetime.now():
                logger.error(f"Token expired on {expiry}")
                return jsonify({'error': 'Token has expired'}), 400
                
            # Get or create usage record
            usage = SearchLog.query.filter_by(token=access_token).first()
            if not usage:
                logger.info("Creating new usage record for token")
                usage = SearchLog(
                    token=access_token,
                    searches_used=0,
                    searches_remaining=int(search_limit),
                    expiry_date=expiry
                )
                db.session.add(usage)
            
            if usage.searches_remaining <= 0:
                logger.error(f"No searches remaining for token (used: {usage.searches_used})")
                return jsonify({'error': 'No searches remaining'}), 400
                
            # Update usage
            usage.searches_used += 1
            usage.searches_remaining -= 1
            usage.last_search_at = datetime.now()
            db.session.commit()
            logger.info(f"Updated usage - remaining: {usage.searches_remaining}, used: {usage.searches_used}")
            
        except Exception as e:
            logger.exception("Error processing token")
            return jsonify({'error': str(e)}), 500
    else:
        logger.info("No token provided - checking free searches")
        
        # Use a combination of cache and database for free searches
        free_searches_key = f'free_searches:{client_ip}'
        
        # Check database first
        usage = SearchLog.query.filter_by(token=f"free:{client_ip}").first()
        if not usage:
            usage = SearchLog(
                token=f"free:{client_ip}",
                searches_used=0,
                searches_remaining=3,
                expiry_date=datetime.now() + timedelta(days=1)
            )
            db.session.add(usage)
            db.session.commit()
        
        # Check if free searches are exhausted
        if usage.searches_remaining <= 0:
            return jsonify({
                'success': False,
                'error': 'Free search limit reached'
            }), 400
        
        # Update usage
        usage.searches_used += 1
        usage.searches_remaining -= 1
        usage.last_search_at = datetime.now()
        db.session.commit()
        
        # Also update cache for quick access
        cache.set(free_searches_key, usage.searches_used)

    # Proceed with search
    person_name = data.get('person_name')
    search_word = data.get('search_word')
    sort_order = data.get('sort_order', 'date')
    time_period = int(data.get('time_period', 730))
    channel_id = data.get('channel_id', None)
    stop_after_first = data.get('stop_after_first', False)
    
    youtube = setup_youtube_api()
    
    model = get_ai_model()
    qa_pipeline = get_qa_pipeline()
    
    # Search for videos
    search_response = search_videos(
        youtube, 
        person_name,
        sort_order=sort_order,
        days_ago=time_period,
        channel_id=channel_id,
        stop_after_first_match=stop_after_first
    )
    
    all_matches = []
    videos_with_transcripts = 0
    total_videos = len(search_response.get('items', []))
    
    for item in search_response['items']:
        video_id = item['id']['videoId']
        video_title = item['snippet']['title']
        channel_title = item['snippet']['channelTitle']
        publish_date = item['snippet']['publishedAt'][:10]
        
        transcript = get_video_transcript(video_id)
        if transcript:
            videos_with_transcripts += 1
            all_chunk_matches = []
            
            for chunk in process_transcript_chunks(transcript):
                ai_results = qa_pipeline(
                    context=chunk,
                    question=f"Where does {person_name} mention {search_word}?"
                )
                if ai_results['score'] > 0.1:
                    all_chunk_matches.append(ai_results)
            
            # After AI processing
            if not all_chunk_matches:
                # Fallback to original keyword search
                matches = search_word_in_transcript(
                    transcript, 
                    search_word,
                    stop_after_first_match=stop_after_first
                )
            else:
                matches = process_ai_results(all_chunk_matches)
            
            for match in matches:
                timestamp = format_timestamp(match['start'])
                ts_url = f"https://youtube.com/watch?v={video_id}&t={int(match['start'])}s"
                
                all_matches.append({
                    'video_id': video_id,
                    'video_title': video_title,
                    'channel_title': channel_title,
                    'publish_date': publish_date,
                    'timestamp': timestamp,
                    'timestamp_seconds': match['start'],
                    'url': ts_url,
                    'context': match['answer']
                })
                
                if stop_after_first and all_matches:
                    break
    
    return jsonify({
        'success': True,
        'matches': all_matches,
        'total_videos': total_videos,
        'videos_with_transcripts': videos_with_transcripts
    })
    
@search_bp.route('/download_clip', methods=['POST'])
def download_clip():
    """Download an audio clip from a YouTube video."""
    try:
        data = request.json
        video_url = f"https://youtube.com/watch?v={data['video_id']}"
        start_time = float(data['timestamp'])
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
        logger.error(f"Download clip error: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        })

@search_bp.route('/clips/<path:filename>')
def download_file(filename):
    return send_file(
        os.path.join('clips', filename),
        as_attachment=True
    )

@search_bp.route('/check_searches', methods=['POST'])
def check_searches():
    """Check remaining searches for a token or free tier."""
    data = request.get_json()
    client_ip = request.headers.get('X-Forwarded-For', request.remote_addr)
    access_token = data.get('access_token')
    
    try:
        if access_token:
            # Check token usage
            usage = SearchLog.query.filter_by(token=access_token).first()
            if usage and usage.is_valid():
                return jsonify({
                    'success': True,
                    'searches_remaining': usage.searches_remaining,
                    'searches_used': usage.searches_used,
                    'expires': usage.expiry_date.isoformat()
                })
        else:
            # Check free tier usage
            usage = SearchLog.query.filter_by(token=f"free:{client_ip}").first()
            if not usage:
                # Create new free tier usage
                usage = SearchLog(
                    token=f"free:{client_ip}",
                    searches_used=0,
                    searches_remaining=3,
                    expiry_date=datetime.now() + timedelta(days=1)
                )
                db.session.add(usage)
                db.session.commit()
            
            if usage.is_valid():
                return jsonify({
                    'success': True,
                    'searches_remaining': usage.searches_remaining,
                    'searches_used': usage.searches_used,
                    'expires': usage.expiry_date.isoformat()
                })
        
        return jsonify({
            'success': False,
            'error': 'No searches remaining'
        })
        
    except Exception as e:
        logger.exception("Error checking searches")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500 

def search_videos(youtube, person_name, **kwargs):
    try:
        # Add proper error handling and logging
        search_response = youtube.search().list(
            q=person_name,
            part='id,snippet',
            maxResults=50,  # Increase from default
            type='video',
            videoCaption='closedCaption'  # Only get videos with captions
        ).execute()
        
        logger.info(f"Found {len(search_response.get('items', []))} videos for {person_name}")
        return search_response
    except Exception as e:
        logger.error(f"YouTube API search error: {str(e)}")
        return {'items': []}

def process_transcript_chunks(transcript, chunk_size=512):
    """Split long transcripts into manageable chunks."""
    for i in range(0, len(transcript), chunk_size):
        yield transcript[i:i+chunk_size]
