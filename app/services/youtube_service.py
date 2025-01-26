"""YouTube API service."""
import os
from googleapiclient.discovery import build
import logging

logger = logging.getLogger(__name__)

class YouTubeService:
    """Service for interacting with YouTube API."""
    
    def __init__(self):
        """Initialize YouTube service."""
        self.api_key = os.getenv('YOUTUBE_API_KEY')
        if not self.api_key:
            raise ValueError("YOUTUBE_API_KEY not configured")
        
        self.youtube = build('youtube', 'v3', developerKey=self.api_key)
    
    def search_videos(self, query: str):
        """Search videos using YouTube API."""
        return self.youtube.search().list(
            q=query,
            part='id,snippet',
            maxResults=10
        ).execute() 