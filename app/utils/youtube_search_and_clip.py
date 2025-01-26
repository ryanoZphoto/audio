import os
import logging
from googleapiclient.discovery import build
from youtube_transcript_api import YouTubeTranscriptApi
import yt_dlp
import hashlib

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(message)s',
    handlers=[
        logging.FileHandler('search_debug.log', mode='w'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

def setup_youtube_api():
    """Initialize YouTube API client."""
    try:
        api_key = os.getenv('YOUTUBE_API_KEY')
        if not api_key:
            logger.error("YouTube API key not found")
            return None
            
        youtube = build('youtube', 'v3', developerKey=api_key)
        # Test the connection
        try:
            youtube.videos().list(part='snippet', id='test').execute()
            return youtube
        except Exception as e:
            logger.error(f"YouTube API connection test failed: {e}")
            return None
            
    except Exception as e:
        logger.error(f"Error setting up YouTube API: {e}")
        return None


def get_video_transcript(video_id):
    """Get transcript for a video."""
    if not video_id:
        logger.error("No video ID provided")
        return None
        
    try:
        transcript_list = YouTubeTranscriptApi.get_transcript(video_id)
        if not transcript_list:
            logger.error(f"No transcript found for video {video_id}")
            return None
        return transcript_list
    except Exception as e:
        logger.error(f"Error getting transcript for video {video_id}: {e}")
        return None


def search_word_in_transcript(transcript, search_query):
    """Search for word/phrase in transcript and return timestamps."""
    if not transcript or not search_query:
        logger.error("Missing transcript or search query")
        return []
        
    matches = []
    try:
        search_query = search_query.lower()
        for entry in transcript:
            if search_query in entry['text'].lower():
                matches.append({
                    'text': entry['text'],
                    'start': entry['start'],
                    'duration': entry['duration']
                })
        return matches
    except Exception as e:
        logger.error(f"Error searching transcript: {e}")
        return []


def download_audio_clip(video_url, start_time, duration=30):
    """Download a portion of a video's audio."""
    if not video_url or start_time < 0 or duration <= 0:
        logger.error("Invalid parameters for audio clip download")
        return None
        
    try:
        output_dir = 'clips'
        os.makedirs(output_dir, exist_ok=True)
        
        clip_id = hashlib.md5(
            f"{video_url}:{start_time}:{duration}".encode()
        ).hexdigest()
        output_path = os.path.join(output_dir, f"{clip_id}.mp3")
        
        if os.path.exists(output_path):
            logger.info(f"Using cached clip: {output_path}")
            return output_path
            
        ydl_opts = {
            'format': 'bestaudio/best',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
            'outtmpl': output_path,
            'quiet': True
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([video_url])
            
        if not os.path.exists(output_path):
            logger.error("Download completed but file not found")
            return None
            
        return output_path
    except Exception as e:
        logger.error(f"Error downloading clip: {e}")
        return None

if __name__ == "__main__":
    print("This script is now meant to be used through the web interface.")
    print("Please run 'python app.py' instead.") 