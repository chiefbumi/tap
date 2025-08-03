"""
YouTube Client for Smart Shower OS
Handles YouTube video search and audio extraction
"""

import asyncio
import logging
import subprocess
import tempfile
import os
from typing import Dict, Any, List, Optional
from pathlib import Path
import yt_dlp


class YouTubeClient:
    """YouTube API client for audio extraction"""
    
    def __init__(self, config):
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # YouTube settings
        self.api_key = config.get_credential('youtube.api_key', '')
        self.client_id = config.get_credential('youtube.client_id', '')
        self.client_secret = config.get_credential('youtube.client_secret', '')
        
        # yt-dlp settings
        self.ydl_opts = {
            'format': 'bestaudio/best',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
            'outtmpl': '%(title)s.%(ext)s',
            'quiet': True,
            'no_warnings': True,
            'extractaudio': True,
            'audioformat': 'mp3',
            'audioquality': '192K'
        }
        
        # Cache
        self.cached_videos = {}
        self.download_cache = {}
        
        # Current playback
        self.current_video = None
        self.is_playing = False
        
    async def initialize(self):
        """Initialize the YouTube client"""
        self.logger.info("Initializing YouTube client...")
        
        # Check if yt-dlp is available
        try:
            subprocess.run(['yt-dlp', '--version'], capture_output=True, check=True)
            self.logger.info("yt-dlp is available")
        except (subprocess.CalledProcessError, FileNotFoundError):
            self.logger.warning("yt-dlp not found - YouTube functionality will be limited")
        
        # Check if ffmpeg is available
        try:
            subprocess.run(['ffmpeg', '-version'], capture_output=True, check=True)
            self.logger.info("ffmpeg is available")
        except (subprocess.CalledProcessError, FileNotFoundError):
            self.logger.warning("ffmpeg not found - audio extraction may not work")
        
        self.logger.info("YouTube client initialized")
    
    async def shutdown(self):
        """Shutdown the YouTube client"""
        self.logger.info("Shutting down YouTube client...")
        
        # Stop playback if active
        if self.is_playing:
            await self.stop_playback()
        
        # Clear cache
        self.cached_videos.clear()
        self.download_cache.clear()
    
    async def search_videos(self, query: str, limit: int = 20) -> List[Dict[str, Any]]:
        """Search for videos on YouTube"""
        try:
            with yt_dlp.YoutubeDL(self.ydl_opts) as ydl:
                # Search for videos
                search_results = ydl.extract_info(f"ytsearch{limit}:{query}", download=False)
                
                videos = []
                for entry in search_results['entries']:
                    if entry:
                        video_info = {
                            'id': entry['id'],
                            'title': entry['title'],
                            'channel': entry.get('uploader', 'Unknown'),
                            'duration': entry.get('duration', 0),
                            'view_count': entry.get('view_count', 0),
                            'url': entry['webpage_url'],
                            'thumbnail': entry.get('thumbnail', ''),
                            'description': entry.get('description', '')[:200] + '...' if entry.get('description') else ''
                        }
                        videos.append(video_info)
                
                self.logger.info(f"Found {len(videos)} videos for query: {query}")
                return videos
                
        except Exception as e:
            self.logger.error(f"Error searching YouTube videos: {e}")
            return []
    
    async def get_video_info(self, video_id: str) -> Optional[Dict[str, Any]]:
        """Get information about a specific video"""
        try:
            with yt_dlp.YoutubeDL(self.ydl_opts) as ydl:
                # Extract video info
                info = ydl.extract_info(f"https://www.youtube.com/watch?v={video_id}", download=False)
                
                video_info = {
                    'id': info['id'],
                    'title': info['title'],
                    'channel': info.get('uploader', 'Unknown'),
                    'duration': info.get('duration', 0),
                    'view_count': info.get('view_count', 0),
                    'url': info['webpage_url'],
                    'thumbnail': info.get('thumbnail', ''),
                    'description': info.get('description', '')[:200] + '...' if info.get('description') else '',
                    'formats': info.get('formats', [])
                }
                
                return video_info
                
        except Exception as e:
            self.logger.error(f"Error getting video info: {e}")
            return None
    
    async def download_audio(self, video_id: str, output_path: str = None) -> Optional[str]:
        """Download audio from a YouTube video"""
        try:
            if output_path is None:
                # Create temporary directory
                temp_dir = tempfile.mkdtemp()
                output_path = os.path.join(temp_dir, '%(title)s.%(ext)s')
            
            # Configure yt-dlp for audio download
            download_opts = self.ydl_opts.copy()
            download_opts['outtmpl'] = output_path
            
            with yt_dlp.YoutubeDL(download_opts) as ydl:
                # Download audio
                info = ydl.extract_info(f"https://www.youtube.com/watch?v={video_id}", download=True)
                
                # Find the downloaded file
                if 'requested_downloads' in info and info['requested_downloads']:
                    downloaded_file = info['requested_downloads'][0]['filepath']
                    self.logger.info(f"Downloaded audio: {downloaded_file}")
                    return downloaded_file
                else:
                    self.logger.error("No audio file downloaded")
                    return None
                
        except Exception as e:
            self.logger.error(f"Error downloading audio: {e}")
            return None
    
    async def play_video(self, video_id: str) -> bool:
        """Play audio from a YouTube video"""
        try:
            # Get video info
            video_info = await self.get_video_info(video_id)
            if not video_info:
                return False
            
            # Download audio
            audio_file = await self.download_audio(video_id)
            if not audio_file:
                return False
            
            # Start playback using system player
            await self._play_audio_file(audio_file)
            
            self.current_video = video_info
            self.is_playing = True
            
            self.logger.info(f"Started playing: {video_info['title']}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error playing video: {e}")
            return False
    
    async def _play_audio_file(self, audio_file: str):
        """Play audio file using system player"""
        try:
            # Use mpv for high-quality audio playback
            cmd = [
                'mpv',
                '--no-video',  # Audio only
                '--volume', '50',
                audio_file
            ]
            
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            # Store process for later control
            self.current_process = process
            
        except Exception as e:
            self.logger.error(f"Error playing audio file: {e}")
    
    async def stop_playback(self) -> bool:
        """Stop current playback"""
        try:
            if hasattr(self, 'current_process') and self.current_process:
                self.current_process.terminate()
                try:
                    await asyncio.wait_for(self.current_process.wait(), timeout=5.0)
                except asyncio.TimeoutError:
                    self.current_process.kill()
                
                self.current_process = None
            
            self.is_playing = False
            self.current_video = None
            
            self.logger.info("Stopped YouTube playback")
            return True
            
        except Exception as e:
            self.logger.error(f"Error stopping playback: {e}")
            return False
    
    async def get_playlist_videos(self, playlist_url: str) -> List[Dict[str, Any]]:
        """Get videos from a YouTube playlist"""
        try:
            with yt_dlp.YoutubeDL(self.ydl_opts) as ydl:
                # Extract playlist info
                info = ydl.extract_info(playlist_url, download=False)
                
                videos = []
                for entry in info['entries']:
                    if entry:
                        video_info = {
                            'id': entry['id'],
                            'title': entry['title'],
                            'channel': entry.get('uploader', 'Unknown'),
                            'duration': entry.get('duration', 0),
                            'url': entry['webpage_url'],
                            'thumbnail': entry.get('thumbnail', '')
                        }
                        videos.append(video_info)
                
                self.logger.info(f"Found {len(videos)} videos in playlist")
                return videos
                
        except Exception as e:
            self.logger.error(f"Error getting playlist videos: {e}")
            return []
    
    async def get_channel_videos(self, channel_url: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Get videos from a YouTube channel"""
        try:
            with yt_dlp.YoutubeDL(self.ydl_opts) as ydl:
                # Extract channel info
                info = ydl.extract_info(channel_url, download=False)
                
                videos = []
                for entry in info['entries'][:limit]:
                    if entry:
                        video_info = {
                            'id': entry['id'],
                            'title': entry['title'],
                            'channel': entry.get('uploader', 'Unknown'),
                            'duration': entry.get('duration', 0),
                            'url': entry['webpage_url'],
                            'thumbnail': entry.get('thumbnail', '')
                        }
                        videos.append(video_info)
                
                self.logger.info(f"Found {len(videos)} videos from channel")
                return videos
                
        except Exception as e:
            self.logger.error(f"Error getting channel videos: {e}")
            return []
    
    async def get_trending_videos(self, category: str = 'music', limit: int = 20) -> List[Dict[str, Any]]:
        """Get trending videos from YouTube"""
        try:
            # YouTube trending URL
            trending_url = f"https://www.youtube.com/feed/trending?bp={category}"
            
            with yt_dlp.YoutubeDL(self.ydl_opts) as ydl:
                # Extract trending videos
                info = ydl.extract_info(trending_url, download=False)
                
                videos = []
                for entry in info['entries'][:limit]:
                    if entry:
                        video_info = {
                            'id': entry['id'],
                            'title': entry['title'],
                            'channel': entry.get('uploader', 'Unknown'),
                            'duration': entry.get('duration', 0),
                            'url': entry['webpage_url'],
                            'thumbnail': entry.get('thumbnail', '')
                        }
                        videos.append(video_info)
                
                self.logger.info(f"Found {len(videos)} trending videos")
                return videos
                
        except Exception as e:
            self.logger.error(f"Error getting trending videos: {e}")
            return []
    
    async def extract_audio_stream(self, video_id: str) -> Optional[str]:
        """Extract audio stream URL without downloading"""
        try:
            with yt_dlp.YoutubeDL(self.ydl_opts) as ydl:
                # Get video info
                info = ydl.extract_info(f"https://www.youtube.com/watch?v={video_id}", download=False)
                
                # Find best audio format
                audio_formats = []
                for format_info in info.get('formats', []):
                    if format_info.get('acodec') != 'none' and format_info.get('vcodec') == 'none':
                        audio_formats.append(format_info)
                
                if audio_formats:
                    # Get the best quality audio format
                    best_audio = max(audio_formats, key=lambda x: x.get('abr', 0))
                    return best_audio['url']
                
                return None
                
        except Exception as e:
            self.logger.error(f"Error extracting audio stream: {e}")
            return None
    
    async def get_video_duration(self, video_id: str) -> Optional[int]:
        """Get video duration in seconds"""
        try:
            video_info = await self.get_video_info(video_id)
            if video_info:
                return video_info.get('duration', 0)
            return None
            
        except Exception as e:
            self.logger.error(f"Error getting video duration: {e}")
            return None
    
    def is_available(self) -> bool:
        """Check if YouTube client is available"""
        try:
            subprocess.run(['yt-dlp', '--version'], capture_output=True, check=True)
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            return False
    
    async def get_status(self) -> Dict[str, Any]:
        """Get YouTube client status"""
        return {
            'available': self.is_available(),
            'is_playing': self.is_playing,
            'current_video': self.current_video,
            'cached_videos': len(self.cached_videos),
            'download_cache': len(self.download_cache)
        }
    
    async def clear_cache(self):
        """Clear download cache"""
        try:
            # Remove cached files
            for file_path in self.download_cache.values():
                if os.path.exists(file_path):
                    os.remove(file_path)
            
            self.download_cache.clear()
            self.cached_videos.clear()
            
            self.logger.info("YouTube cache cleared")
            
        except Exception as e:
            self.logger.error(f"Error clearing cache: {e}")
    
    async def get_download_progress(self, video_id: str) -> Optional[Dict[str, Any]]:
        """Get download progress for a video"""
        # This would track download progress in a real implementation
        return {
            'video_id': video_id,
            'status': 'downloading',
            'progress': 0.0,
            'speed': 0.0,
            'eta': 0
        } 