import os
import datetime
from googleapiclient.discovery import build
from youtube_transcript_api import YouTubeTranscriptApi
from dotenv import load_dotenv
import yt_dlp
import subprocess
import re
import logging
from flask import Flask, request, jsonify, render_template
import hashlib
import hmac

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(message)s',
    handlers=[
        logging.FileHandler('search_debug.log', mode='w'),
        logging.StreamHandler()
    ]
)

app = Flask(__name__)

# Secret key for token generation (store this securely in production)
TOKEN_SECRET = os.getenv('TOKEN_SECRET', 'your-secret-key-here')

def setup_youtube_api():
    """Setup YouTube API client."""
    load_dotenv()
    api_key = os.getenv('YOUTUBE_API_KEY')
    if not api_key:
        raise ValueError("Please set YOUTUBE_API_KEY in .env file")
    return build('youtube', 'v3', developerKey=api_key)


def search_videos(youtube, query, sort_order='date', days_ago=730, 
                 channel_id=None, max_results=50, stop_after_first_match=False):
    """Search for videos matching the query."""
    search_params = {
        'q': query,
        'part': 'id,snippet',
        'maxResults': max_results,
        'type': 'video',
        'videoCaption': 'closedCaption',
        'relevanceLanguage': 'en',
        'order': sort_order
    }
    
    if days_ago > 0:
        published_after = (
            datetime.datetime.utcnow() - 
            datetime.timedelta(days=days_ago)
        ).strftime('%Y-%m-%dT%H:%M:%SZ')
        search_params['publishedAfter'] = published_after
    
    if channel_id:
        search_params['channelId'] = channel_id
    
    request = youtube.search().list(**search_params)
    return request.execute()


def get_video_transcript(video_id):
    """Get transcript for a video."""
    try:
        transcript = YouTubeTranscriptApi.get_transcripts(
            [video_id], 
            languages=['en']
        )[0][video_id]
        return transcript
    except Exception:
        try:
            transcript = YouTubeTranscriptApi.get_transcript(
                video_id,
                languages=['en']
            )
            return transcript
        except Exception:
            return None


def normalize_text(text):
    """Normalize text for comparison."""
    # Remove punctuation and extra spaces
    text = re.sub(r'[^\w\s]', '', text.lower())
    # Replace multiple spaces with single space
    text = re.sub(r'\s+', ' ', text).strip()
    return text


def get_context(transcript, current_idx, window=3):
    """Get context around a transcript entry with larger window."""
    start = max(0, current_idx - window)
    end = min(len(transcript), current_idx + window + 1)
    
    # Get surrounding entries
    context_entries = transcript[start:end]
    
    # Format with timestamps
    context_texts = []
    center_idx = current_idx - start  # Adjust index for the sliced context
    
    for i, entry in enumerate(context_entries):
        if i == center_idx:  # This is the matching entry
            text = f">> [{format_timestamp(entry['start'])}] {entry['text']} <<"
        else:
            text = f"[{format_timestamp(entry['start'])}] {entry['text']}"
        context_texts.append(text)
    
    # Always put the matching text first, followed by before and after context
    if center_idx > 0:  # If there's context before
        before_context = context_texts[:center_idx]
        after_context = context_texts[center_idx + 1:]
        return f"{context_texts[center_idx]} | Before: {' '.join(before_context)} | After: {' '.join(after_context)}"
    else:
        after_context = context_texts[1:]
        return f"{context_texts[0]} | After: {' '.join(after_context)}"


def find_phrase_in_text(search_phrase, text, min_words=1):
    """Check if phrase appears in text with various matching strategies."""
    # Log the comparison
    logging.debug(f"\nComparing phrase: '{search_phrase}' with text: '{text}'")
    
    # Normalize both texts
    norm_phrase = normalize_text(search_phrase)
    norm_text = normalize_text(text)
    
    # Split into words
    phrase_words = norm_phrase.split()
    text_words = norm_text.split()
    
    # For single words, do simple contains check
    if len(phrase_words) == 1:
        for word in text_words:
            if phrase_words[0] in word.lower():
                logging.debug("✓ Found single word match")
                return True
        return False
    
    # For phrases, first try exact match
    if norm_phrase in norm_text:
        logging.debug("✓ Found direct match")
        return True
    
    # Then try matching consecutive words with more flexibility
    text_str = ' '.join(text_words).lower()
    phrase_str = ' '.join(phrase_words).lower()
    if phrase_str in text_str:
        logging.debug("✓ Found phrase match")
        return True
    
    # Try matching with flexible word boundaries and partial matches
    text_str_no_spaces = ''.join(text_words).lower()
    phrase_str_no_spaces = ''.join(phrase_words).lower()
    if phrase_str_no_spaces in text_str_no_spaces:
        logging.debug("✓ Found sequence match")
        return True
    
    logging.debug("✗ No match found")
    return False


def combine_transcript_entries(transcript, window_size=3):
    """Combine transcript entries with overlap for better phrase matching."""
    combined = []
    seen_timestamps = set()  # Track timestamps we've already matched
    
    for i in range(len(transcript)):
        # Get text from surrounding entries
        start_idx = max(0, i - window_size)
        end_idx = min(len(transcript), i + window_size + 1)
        
        # Combine the text with timestamps
        entries = transcript[start_idx:end_idx]
        combined_text = ' '.join(entry['text'] for entry in entries)
        
        # Only include if we haven't seen this timestamp
        current_timestamp = transcript[i]['start']
        if current_timestamp not in seen_timestamps:
            combined.append({
                'index': i,
                'text': combined_text,
                'original': transcript[i],
                'timestamp': current_timestamp
            })
            seen_timestamps.add(current_timestamp)
    
    return combined


def search_word_in_transcript(transcript, search_word, stop_after_first_match=False):
    """Search for specific word or phrase in transcript and return timestamps."""
    if not transcript:
        return []
    
    logging.info(f"\nSearching for phrase: '{search_word}'")
    
    # Create variations of the search term
    search_variations = [
        search_word,  # Original
        search_word.lower(),  # Lowercase
    ]
    
    # Combine transcript entries with overlap
    combined_entries = combine_transcript_entries(transcript, window_size=5)  # Increased window
    logging.info(f"Created {len(combined_entries)} combined transcript entries")
    
    # Track unique matches by timestamp
    results = []
    seen_timestamps = set()
    
    # Search through combined entries
    for entry in combined_entries:
        timestamp = entry['timestamp']
        
        # Skip if we've already found a match at this timestamp
        if timestamp in seen_timestamps:
            continue
        
        # Check all variations
        for variation in search_variations:
            if find_phrase_in_text(variation, entry['text']):
                logging.info(
                    f"\nFound match at {format_timestamp(timestamp)}:"
                    f"\nContext: {entry['text']}"
                )
                
                results.append({
                    'timestamp': timestamp,
                    'text': get_context(transcript, entry['index']),
                    'duration': entry['original']['duration'],
                    'original_text': entry['original']['text']
                })
                seen_timestamps.add(timestamp)
                
                # Stop after first match if requested
                if stop_after_first_match:
                    logging.info("Stopping after first match as requested")
                    return results
                break
    
    logging.info(f"\nFound {len(results)} unique matches")
    return results


def format_timestamp(seconds):
    """Convert seconds to HH:MM:SS format."""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    seconds = int(seconds % 60)
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}"


def download_audio_clip(video_url, start_time, duration=1.0, output_dir="clips"):
    """Download a specific segment of audio from a YouTube video."""
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    try:
        video_id = video_url.split('v=')[1].split('&')[0]
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = os.path.join(
            output_dir, 
            f"clip_{video_id}_{int(start_time)}s_{timestamp}.mp3"
        )
        
        ydl_opts = {
            'format': 'bestaudio/best',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
            'quiet': True,
            'no_warnings': True,
            'extract_audio': True,
            'outtmpl': f'temp_{video_id}.%(ext)s'
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.extract_info(video_url, download=True)
            temp_file = f"temp_{video_id}.mp3"
        
        subprocess.run([
            'ffmpeg',
            '-i', temp_file,
            '-ss', f"{start_time:.3f}",
            '-t', f"{duration:.3f}",
            '-c', 'copy',
            output_file
        ], capture_output=True)
        
        os.remove(temp_file)
        return output_file
        
    except Exception as e:
        print(f"An error occurred: {str(e)}")
        return None


def generate_token(plan_type, expiry_date):
    """Generate a token for a specific plan"""
    message = f"{plan_type}:{expiry_date}".encode()
    signature = hmac.new(TOKEN_SECRET.encode(), message, hashlib.sha256).hexdigest()
    return f"{plan_type}:{expiry_date}:{signature}"

def validate_token(token):
    """Validate a token and return plan details if valid"""
    try:
        plan_type, expiry_date, signature = token.split(':')
        message = f"{plan_type}:{expiry_date}".encode()
        expected_signature = hmac.new(TOKEN_SECRET.encode(), message, hashlib.sha256).hexdigest()
        
        if hmac.compare_digest(signature, expected_signature):
            expiry = datetime.fromisoformat(expiry_date)
            if expiry > datetime.now():
                return {
                    'valid': True,
                    'plan': plan_type,
                    'expiry': expiry
                }
    except:
        pass
    return {'valid': False}

@app.route('/search', methods=['POST'])
def search():
    data = request.json
    token = data.get('access_token', '').strip()
    
    # Validate token if provided
    if token:
        token_data = validate_token(token)
        if not token_data['valid']:
            return jsonify({
                'success': False,
                'error': 'Invalid or expired token'
            })
    
    # Continue with existing search logic
    youtube = setup_youtube_api()
    query = data['query']
    sort_order = data['sort_order']
    days_ago = data['days_ago']
    channel_id = data['channel_id']
    max_results = data['max_results']
    stop_after_first_match = data['stop_after_first_match']
    
    search_results = search_videos(youtube, query, sort_order, days_ago, channel_id, max_results, stop_after_first_match)
    return jsonify({
        'success': True,
        'results': search_results
    })

@app.route('/generate_token', methods=['POST'])
def create_token():
    """Generate a new token (this would be called after Stripe payment confirmation)"""
    data = request.json
    plan_type = data['plan']  # 'day', 'week', or 'month'
    
    expiry_dates = {
        'day': datetime.timedelta(days=1),
        'week': datetime.timedelta(days=7),
        'month': datetime.timedelta(days=30)
    }
    
    expiry = datetime.datetime.now() + expiry_dates[plan_type]
    token = generate_token(plan_type, expiry.isoformat())
    
    return jsonify({
        'success': True,
        'token': token,
        'expiry': expiry.isoformat()
    })

if __name__ == "__main__":
    print("This script is now meant to be used through the web interface.")
    print("Please run 'python app.py' instead.") 