"""
Audio Manager for Smart Shower
Handles Spotify, YouTube, and local music playback
"""

import asyncio
import logging
import subprocess
import time
from typing import Optional, Callable, Dict, Any
from enum import Enum
from dataclasses import dataclass
from pathlib import Path


class AudioSource(Enum):
    """Audio source types"""
    SPOTIFY = "spotify"
    YOUTUBE = "youtube"
    LOCAL = "local"
    BLUETOOTH = "bluetooth"


class PlaybackState(Enum):
    """Audio playback states"""
    STOPPED = "stopped"
    PLAYING = "playing"
    PAUSED = "paused"
    LOADING = "loading"


@dataclass
class AudioTrack:
    """Audio track information"""
    title: str
    artist: str = ""
    album: str = ""
    duration: int = 0
    source: AudioSource = AudioSource.LOCAL
    url: str = ""
    local_path: str = ""


class AudioManager:
    """Manages audio playback from multiple sources"""
    
    def __init__(self, config):
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Audio state
        self.current_track: Optional[AudioTrack] = None
        self.playback_state = PlaybackState.STOPPED
        self.volume = 50  # 0-100
        self.is_muted = False
        
        # Audio sources
        self.spotify_client = None
        self.youtube_client = None
        self.bluetooth_client = None
        
        # Playback process
        self.playback_process = None
        self.current_source = None
        
        # Event callbacks
        self.on_playback_start: Optional[Callable] = None
        self.on_playback_stop: Optional[Callable] = None
        self.on_playback_pause: Optional[Callable] = None
        self.on_playback_resume: Optional[Callable] = None
        self.on_track_change: Optional[Callable] = None
        self.on_volume_change: Optional[Callable] = None
        
        # Control loop
        self.control_task = None
        self.is_running = False
        
        # Audio output configuration
        self.audio_device = "default"
        self.audio_format = "mp3"
        self.sample_rate = 44100
        
    async def initialize(self):
        """Initialize the audio manager"""
        self.logger.info("Initializing audio manager...")
        
        # Initialize audio sources
        await self._initialize_audio_sources()
        
        # Load settings
        await self._load_settings()
        
        # Initialize audio system
        await self._initialize_audio_system()
        
        self.logger.info("Audio manager initialized")
    
    async def _initialize_audio_sources(self):
        """Initialize audio source clients"""
        # Initialize Spotify client
        from services.spotify_client import SpotifyClient
        self.spotify_client = SpotifyClient(self.config)
        await self.spotify_client.initialize()
        
        # Initialize YouTube client
        from services.youtube_client import YouTubeClient
        self.youtube_client = YouTubeClient(self.config)
        await self.youtube_client.initialize()
        
        # Initialize Bluetooth client
        from services.bluetooth_client import BluetoothClient
        self.bluetooth_client = BluetoothClient(self.config)
        await self.bluetooth_client.initialize()
        
        self.logger.info("Audio sources initialized")
    
    async def _load_settings(self):
        """Load audio settings from config"""
        settings = self.config.get('audio', {})
        self.volume = settings.get('default_volume', 50)
        self.audio_device = settings.get('audio_device', 'default')
        self.audio_format = settings.get('audio_format', 'mp3')
        self.sample_rate = settings.get('sample_rate', 44100)
        
        self.logger.info(f"Loaded audio settings - Volume: {self.volume}%")
    
    async def _initialize_audio_system(self):
        """Initialize the audio system"""
        # In a real system, this would:
        # - Configure ALSA/PulseAudio
        # - Set up audio routing
        # - Configure Bluetooth audio
        # - Test audio output
        
        self.logger.info("Audio system initialized")
    
    async def start(self):
        """Start the audio manager"""
        self.logger.info("Starting audio manager...")
        self.is_running = True
        
        # Start control loop
        self.control_task = asyncio.create_task(self._control_loop())
        
        self.logger.info("Audio manager started")
    
    async def shutdown(self):
        """Shutdown the audio manager"""
        self.logger.info("Shutting down audio manager...")
        self.is_running = False
        
        # Stop playback
        await self.stop_playback()
        
        # Cancel control task
        if self.control_task:
            self.control_task.cancel()
            try:
                await self.control_task
            except asyncio.CancelledError:
                pass
        
        # Shutdown clients
        if self.spotify_client:
            await self.spotify_client.shutdown()
        if self.youtube_client:
            await self.youtube_client.shutdown()
        if self.bluetooth_client:
            await self.bluetooth_client.shutdown()
        
        self.logger.info("Audio manager shutdown complete")
    
    async def start_playback(self, source: str, track_info: Dict[str, Any] = None):
        """Start audio playback from specified source"""
        self.logger.info(f"Starting playback from {source}")
        
        try:
            # Parse source
            if source.startswith('spotify:'):
                await self._play_spotify(source)
            elif source.startswith('youtube:'):
                await self._play_youtube(source)
            elif source.startswith('local:'):
                await self._play_local(source)
            elif source.startswith('bluetooth:'):
                await self._play_bluetooth(source)
            else:
                # Default to local file
                await self._play_local(f"local:{source}")
            
            self.playback_state = PlaybackState.LOADING
            
            # Trigger event
            if self.on_playback_start:
                await self.on_playback_start(source)
            
        except Exception as e:
            self.logger.error(f"Failed to start playback: {e}")
            raise
    
    async def stop_playback(self):
        """Stop audio playback"""
        self.logger.info("Stopping audio playback...")
        
        # Stop playback process
        if self.playback_process:
            self.playback_process.terminate()
            try:
                await asyncio.wait_for(self.playback_process.wait(), timeout=5.0)
            except asyncio.TimeoutError:
                self.playback_process.kill()
            self.playback_process = None
        
        self.playback_state = PlaybackState.STOPPED
        self.current_track = None
        
        # Trigger event
        if self.on_playback_stop:
            await self.on_playback_stop()
        
        self.logger.info("Audio playback stopped")
    
    async def pause_playback(self):
        """Pause audio playback"""
        if self.playback_state == PlaybackState.PLAYING:
            self.logger.info("Pausing audio playback...")
            
            # Pause playback process
            if self.playback_process:
                self.playback_process.send_signal(subprocess.signal.SIGSTOP)
            
            self.playback_state = PlaybackState.PAUSED
            
            # Trigger event
            if self.on_playback_pause:
                await self.on_playback_pause()
    
    async def resume_playback(self):
        """Resume audio playback"""
        if self.playback_state == PlaybackState.PAUSED:
            self.logger.info("Resuming audio playback...")
            
            # Resume playback process
            if self.playback_process:
                self.playback_process.send_signal(subprocess.signal.SIGCONT)
            
            self.playback_state = PlaybackState.PLAYING
            
            # Trigger event
            if self.on_playback_resume:
                await self.on_playback_resume()
    
    async def set_volume(self, volume: int):
        """Set audio volume (0-100)"""
        volume = max(0, min(100, volume))
        
        if volume != self.volume:
            self.logger.info(f"Setting volume to {volume}%")
            self.volume = volume
            
            # Update system volume
            await self._set_system_volume(volume)
            
            # Trigger event
            if self.on_volume_change:
                await self.on_volume_change(volume)
    
    async def mute(self):
        """Mute audio"""
        self.logger.info("Muting audio...")
        self.is_muted = True
        await self._set_system_volume(0)
    
    async def unmute(self):
        """Unmute audio"""
        self.logger.info("Unmuting audio...")
        self.is_muted = False
        await self._set_system_volume(self.volume)
    
    async def get_status(self):
        """Get current audio status"""
        return {
            'playback_state': self.playback_state.value,
            'current_track': self.current_track.__dict__ if self.current_track else None,
            'volume': self.volume,
            'is_muted': self.is_muted,
            'current_source': self.current_source
        }
    
    async def _play_spotify(self, source: str):
        """Play audio from Spotify"""
        track_id = source.replace('spotify:', '')
        
        self.logger.info(f"Playing Spotify track: {track_id}")
        
        # Get track info from Spotify
        track_info = await self.spotify_client.get_track_info(track_id)
        
        # Create audio track object
        self.current_track = AudioTrack(
            title=track_info.get('name', 'Unknown'),
            artist=track_info.get('artist', 'Unknown'),
            album=track_info.get('album', ''),
            duration=track_info.get('duration_ms', 0) // 1000,
            source=AudioSource.SPOTIFY,
            url=track_info.get('preview_url', '')
        )
        
        # Start playback using Spotify client
        await self.spotify_client.play_track(track_id)
        self.current_source = AudioSource.SPOTIFY
        self.playback_state = PlaybackState.PLAYING
    
    async def _play_youtube(self, source: str):
        """Play audio from YouTube"""
        video_id = source.replace('youtube:', '')
        
        self.logger.info(f"Playing YouTube video: {video_id}")
        
        # Get video info from YouTube
        video_info = await self.youtube_client.get_video_info(video_id)
        
        # Create audio track object
        self.current_track = AudioTrack(
            title=video_info.get('title', 'Unknown'),
            artist=video_info.get('channel', 'Unknown'),
            duration=video_info.get('duration', 0),
            source=AudioSource.YOUTUBE,
            url=f"https://youtube.com/watch?v={video_id}"
        )
        
        # Start playback using YouTube client
        await self.youtube_client.play_video(video_id)
        self.current_source = AudioSource.YOUTUBE
        self.playback_state = PlaybackState.PLAYING
    
    async def _play_local(self, source: str):
        """Play local audio file"""
        file_path = source.replace('local:', '')
        
        self.logger.info(f"Playing local file: {file_path}")
        
        # Check if file exists
        if not Path(file_path).exists():
            raise FileNotFoundError(f"Audio file not found: {file_path}")
        
        # Get file info
        file_info = await self._get_file_info(file_path)
        
        # Create audio track object
        self.current_track = AudioTrack(
            title=file_info.get('title', Path(file_path).stem),
            duration=file_info.get('duration', 0),
            source=AudioSource.LOCAL,
            local_path=file_path
        )
        
        # Start playback using local player
        await self._play_local_file(file_path)
        self.current_source = AudioSource.LOCAL
        self.playback_state = PlaybackState.PLAYING
    
    async def _play_bluetooth(self, source: str):
        """Play audio via Bluetooth"""
        device_id = source.replace('bluetooth:', '')
        
        self.logger.info(f"Playing via Bluetooth device: {device_id}")
        
        # Connect to Bluetooth device
        await self.bluetooth_client.connect(device_id)
        
        # Start Bluetooth audio
        await self.bluetooth_client.start_audio()
        self.current_source = AudioSource.BLUETOOTH
        self.playback_state = PlaybackState.PLAYING
    
    async def _play_local_file(self, file_path: str):
        """Play local audio file using system player"""
        # Use mpv for high-quality audio playback
        cmd = [
            'mpv',
            '--no-video',  # Audio only
            '--volume', str(self.volume),
            '--audio-device', self.audio_device,
            file_path
        ]
        
        self.playback_process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
    
    async def _get_file_info(self, file_path: str):
        """Get information about audio file"""
        # Use ffprobe to get file info
        cmd = [
            'ffprobe',
            '-v', 'quiet',
            '-print_format', 'json',
            '-show_format',
            file_path
        ]
        
        try:
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await process.communicate()
            
            if process.returncode == 0:
                import json
                info = json.loads(stdout.decode())
                format_info = info.get('format', {})
                
                return {
                    'duration': float(format_info.get('duration', 0)),
                    'bitrate': int(format_info.get('bit_rate', 0)),
                    'format': format_info.get('format_name', '')
                }
        except Exception as e:
            self.logger.warning(f"Could not get file info: {e}")
        
        return {}
    
    async def _set_system_volume(self, volume: int):
        """Set system audio volume"""
        # Use amixer to control system volume
        cmd = ['amixer', 'set', 'Master', f'{volume}%']
        
        try:
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            await process.communicate()
        except Exception as e:
            self.logger.warning(f"Could not set system volume: {e}")
    
    async def _control_loop(self):
        """Main control loop for audio management"""
        while self.is_running:
            try:
                # Monitor playback process
                if self.playback_process:
                    if self.playback_process.returncode is not None:
                        # Process finished
                        self.logger.info("Playback process finished")
                        self.playback_state = PlaybackState.STOPPED
                        self.current_track = None
                        self.playback_process = None
                
                # Update playback state
                if self.playback_state == PlaybackState.LOADING:
                    # Check if playback has started
                    if self.playback_process and self.playback_process.returncode is None:
                        self.playback_state = PlaybackState.PLAYING
                
                await asyncio.sleep(0.1)  # 100ms control loop
                
            except Exception as e:
                self.logger.error(f"Error in audio control loop: {e}")
                await asyncio.sleep(1)
    
    async def search_spotify(self, query: str):
        """Search Spotify for tracks"""
        return await self.spotify_client.search_tracks(query)
    
    async def search_youtube(self, query: str):
        """Search YouTube for videos"""
        return await self.youtube_client.search_videos(query)
    
    async def get_local_tracks(self, directory: str = None):
        """Get list of local audio files"""
        if directory is None:
            directory = self.config.get('audio', {}).get('local_music_path', './music')
        
        music_dir = Path(directory)
        if not music_dir.exists():
            return []
        
        # Find audio files
        audio_extensions = {'.mp3', '.wav', '.flac', '.m4a', '.ogg'}
        tracks = []
        
        for file_path in music_dir.rglob('*'):
            if file_path.suffix.lower() in audio_extensions:
                tracks.append({
                    'path': str(file_path),
                    'name': file_path.stem,
                    'size': file_path.stat().st_size
                })
        
        return tracks
    
    async def get_bluetooth_devices(self):
        """Get list of available Bluetooth devices"""
        return await self.bluetooth_client.get_devices()
    
    async def connect_bluetooth(self, device_id: str):
        """Connect to Bluetooth device"""
        return await self.bluetooth_client.connect(device_id)
    
    async def disconnect_bluetooth(self):
        """Disconnect from Bluetooth device"""
        return await self.bluetooth_client.disconnect() 