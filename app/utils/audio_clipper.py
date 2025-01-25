import yt_dlp
import subprocess
import os
from datetime import datetime


def parse_timestamp(timestamp):
    """Convert timestamp string to seconds."""
    try:
        # Handle HH:MM:SS format
        if timestamp.count(':') == 2:
            h, m, s = map(float, timestamp.split(':'))
            return h * 3600 + m * 60 + s
        # Handle MM:SS format
        elif timestamp.count(':') == 1:
            m, s = map(float, timestamp.split(':'))
            return m * 60 + s
        # Handle seconds format
        else:
            return float(timestamp)
    except ValueError:
        raise ValueError("Invalid timestamp format. Use HH:MM:SS, MM:SS, or seconds")


def format_filename(video_id, start_time, duration):
    """Create a descriptive filename."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"clip_{video_id}_{int(start_time)}s_to_{int(start_time + duration)}s_{timestamp}.mp3"


def download_audio_clip(video_url, start_time, duration=1.0, output_dir="clips"):
    """Download a specific segment of audio from a YouTube video."""
    
    # Create output directory if it doesn't exist
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # Convert timestamp to seconds if it's a string
    if isinstance(start_time, str):
        start_seconds = parse_timestamp(start_time)
    else:
        start_seconds = float(start_time)
    
    # Ensure duration is a float
    duration = float(duration)
    
    try:
        # Extract video ID from URL
        video_id = video_url.split('v=')[1].split('&')[0]
        
        # Generate output filename
        output_file = os.path.join(output_dir, format_filename(video_id, start_seconds, duration))
        
        # Download options
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
        
        print("Downloading audio...")
        # Download full audio
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(video_url, download=True)
            temp_file = f"temp_{video_id}.mp3"
        
        print(f"Extracting clip from {start_seconds:.2f}s to {start_seconds + duration:.2f}s...")
        # Cut the specific segment using ffmpeg
        subprocess.run([
            'ffmpeg',
            '-i', temp_file,
            '-ss', f"{start_seconds:.3f}",  # More precise timestamp
            '-t', f"{duration:.3f}",        # More precise duration
            '-c', 'copy',
            output_file
        ], capture_output=True)
        
        # Clean up temporary file
        os.remove(temp_file)
        
        print(f"Successfully saved clip to: {output_file}")
        return output_file
        
    except Exception as e:
        print(f"An error occurred: {str(e)}")
        return None


def main():
    print("YouTube Audio Clipper")
    print("--------------------")
    print("Enter the details of the clip you want to extract:")
    
    video_url = input("Video URL: ")
    timestamp = input("Timestamp (HH:MM:SS or MM:SS): ")
    
    # More precise duration control
    print("\nDuration options:")
    print("1. Enter exact duration in seconds (e.g., 1.5)")
    print("2. Enter end timestamp (HH:MM:SS or MM:SS)")
    duration_choice = input("Choose option (1 or 2): ")
    
    if duration_choice == "1":
        duration = float(input("Enter duration in seconds: "))
    else:
        end_timestamp = input("Enter end timestamp: ")
        start_seconds = parse_timestamp(timestamp)
        end_seconds = parse_timestamp(end_timestamp)
        duration = end_seconds - start_seconds
    
    # Download the clip
    output_file = download_audio_clip(video_url, timestamp, duration)
    
    if output_file:
        print("\nDone! You can find your clip at:", output_file)


if __name__ == "__main__":
    main() 