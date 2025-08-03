"""
Spotify Client for Smart Shower OS
Handles Spotify authentication and music playback
"""

import asyncio
import logging
import time
from typing import Dict, Any, List, Optional
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from spotipy.exceptions import SpotifyException


class SpotifyClient:
    """Spotify API client for music playback"""
    
    def __init__(self, config):
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Spotify credentials
        self.client_id = config.get_credential('spotify.client_id', '')
        self.client_secret = config.get_credential('spotify.client_secret', '')
        self.redirect_uri = config.get_credential('spotify.redirect_uri', 'http://localhost:8080/callback')
        
        # Spotify client
        self.sp = None
        self.is_authenticated = False
        self.current_user = None
        
        # Playback state
        self.current_track = None
        self.current_playlist = None
        self.is_playing = False
        
        # Cache
        self.cached_playlists = {}
        self.cached_tracks = {}
        
    async def initialize(self):
        """Initialize the Spotify client"""
        self.logger.info("Initializing Spotify client...")
        
        if not self.client_id or not self.client_secret:
            self.logger.warning("Spotify credentials not configured - client will be disabled")
            return
        
        try:
            # Create Spotify client
            self.sp = spotipy.Spotify(
                auth_manager=SpotifyOAuth(
                    client_id=self.client_id,
                    client_secret=self.client_secret,
                    redirect_uri=self.redirect_uri,
                    scope='user-read-playback-state user-modify-playback-state user-read-currently-playing playlist-read-private user-library-read'
                )
            )
            
            # Test authentication
            await self._test_authentication()
            
            self.logger.info("Spotify client initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize Spotify client: {e}")
            self.sp = None
    
    async def _test_authentication(self):
        """Test Spotify authentication"""
        try:
            # Get current user
            self.current_user = self.sp.current_user()
            self.is_authenticated = True
            
            self.logger.info(f"Authenticated as Spotify user: {self.current_user['display_name']}")
            
        except SpotifyException as e:
            self.logger.error(f"Spotify authentication failed: {e}")
            self.is_authenticated = False
    
    async def shutdown(self):
        """Shutdown the Spotify client"""
        self.logger.info("Shutting down Spotify client...")
        
        # Stop playback if active
        if self.is_playing:
            await self.stop_playback()
        
        self.sp = None
        self.is_authenticated = False
    
    async def search_tracks(self, query: str, limit: int = 20) -> List[Dict[str, Any]]:
        """Search for tracks on Spotify"""
        if not self.is_authenticated:
            return []
        
        try:
            results = self.sp.search(q=query, type='track', limit=limit)
            tracks = []
            
            for track in results['tracks']['items']:
                track_info = {
                    'id': track['id'],
                    'name': track['name'],
                    'artist': track['artists'][0]['name'] if track['artists'] else 'Unknown',
                    'album': track['album']['name'],
                    'duration_ms': track['duration_ms'],
                    'preview_url': track['preview_url'],
                    'uri': track['uri']
                }
                tracks.append(track_info)
            
            self.logger.info(f"Found {len(tracks)} tracks for query: {query}")
            return tracks
            
        except Exception as e:
            self.logger.error(f"Error searching Spotify tracks: {e}")
            return []
    
    async def get_track_info(self, track_id: str) -> Optional[Dict[str, Any]]:
        """Get information about a specific track"""
        if not self.is_authenticated:
            return None
        
        try:
            track = self.sp.track(track_id)
            
            track_info = {
                'id': track['id'],
                'name': track['name'],
                'artist': track['artists'][0]['name'] if track['artists'] else 'Unknown',
                'album': track['album']['name'],
                'duration_ms': track['duration_ms'],
                'preview_url': track['preview_url'],
                'uri': track['uri']
            }
            
            return track_info
            
        except Exception as e:
            self.logger.error(f"Error getting track info: {e}")
            return None
    
    async def get_user_playlists(self) -> List[Dict[str, Any]]:
        """Get user's playlists"""
        if not self.is_authenticated:
            return []
        
        try:
            playlists = self.sp.current_user_playlists()
            playlist_list = []
            
            for playlist in playlists['items']:
                playlist_info = {
                    'id': playlist['id'],
                    'name': playlist['name'],
                    'description': playlist.get('description', ''),
                    'tracks_count': playlist['tracks']['total'],
                    'uri': playlist['uri']
                }
                playlist_list.append(playlist_info)
            
            self.logger.info(f"Found {len(playlist_list)} playlists")
            return playlist_list
            
        except Exception as e:
            self.logger.error(f"Error getting user playlists: {e}")
            return []
    
    async def get_playlist_tracks(self, playlist_id: str) -> List[Dict[str, Any]]:
        """Get tracks from a playlist"""
        if not self.is_authenticated:
            return []
        
        try:
            results = self.sp.playlist_tracks(playlist_id)
            tracks = []
            
            for item in results['items']:
                track = item['track']
                if track:
                    track_info = {
                        'id': track['id'],
                        'name': track['name'],
                        'artist': track['artists'][0]['name'] if track['artists'] else 'Unknown',
                        'album': track['album']['name'],
                        'duration_ms': track['duration_ms'],
                        'uri': track['uri']
                    }
                    tracks.append(track_info)
            
            self.logger.info(f"Found {len(tracks)} tracks in playlist")
            return tracks
            
        except Exception as e:
            self.logger.error(f"Error getting playlist tracks: {e}")
            return []
    
    async def play_track(self, track_id: str) -> bool:
        """Play a specific track"""
        if not self.is_authenticated:
            self.logger.warning("Not authenticated with Spotify")
            return False
        
        try:
            # Get track info
            track_info = await self.get_track_info(track_id)
            if not track_info:
                return False
            
            # Start playback
            self.sp.start_playback(uris=[track_info['uri']])
            
            self.current_track = track_info
            self.is_playing = True
            
            self.logger.info(f"Started playing: {track_info['name']} by {track_info['artist']}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error playing track: {e}")
            return False
    
    async def play_playlist(self, playlist_id: str, track_index: int = 0) -> bool:
        """Play a playlist starting from a specific track"""
        if not self.is_authenticated:
            return False
        
        try:
            # Get playlist tracks
            tracks = await self.get_playlist_tracks(playlist_id)
            if not tracks or track_index >= len(tracks):
                return False
            
            # Start playback from specific track
            track_uris = [track['uri'] for track in tracks[track_index:]]
            self.sp.start_playback(uris=track_uris)
            
            self.current_track = tracks[track_index]
            self.current_playlist = playlist_id
            self.is_playing = True
            
            self.logger.info(f"Started playing playlist from track {track_index}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error playing playlist: {e}")
            return False
    
    async def pause_playback(self) -> bool:
        """Pause current playback"""
        if not self.is_authenticated:
            return False
        
        try:
            self.sp.pause_playback()
            self.is_playing = False
            
            self.logger.info("Paused Spotify playback")
            return True
            
        except Exception as e:
            self.logger.error(f"Error pausing playback: {e}")
            return False
    
    async def resume_playback(self) -> bool:
        """Resume current playback"""
        if not self.is_authenticated:
            return False
        
        try:
            self.sp.start_playback()
            self.is_playing = True
            
            self.logger.info("Resumed Spotify playback")
            return True
            
        except Exception as e:
            self.logger.error(f"Error resuming playback: {e}")
            return False
    
    async def stop_playback(self) -> bool:
        """Stop current playback"""
        if not self.is_authenticated:
            return False
        
        try:
            self.sp.pause_playback()
            self.is_playing = False
            self.current_track = None
            self.current_playlist = None
            
            self.logger.info("Stopped Spotify playback")
            return True
            
        except Exception as e:
            self.logger.error(f"Error stopping playback: {e}")
            return False
    
    async def skip_to_next(self) -> bool:
        """Skip to next track"""
        if not self.is_authenticated:
            return False
        
        try:
            self.sp.next_track()
            self.logger.info("Skipped to next track")
            return True
            
        except Exception as e:
            self.logger.error(f"Error skipping to next track: {e}")
            return False
    
    async def skip_to_previous(self) -> bool:
        """Skip to previous track"""
        if not self.is_authenticated:
            return False
        
        try:
            self.sp.previous_track()
            self.logger.info("Skipped to previous track")
            return True
            
        except Exception as e:
            self.logger.error(f"Error skipping to previous track: {e}")
            return False
    
    async def set_volume(self, volume: int) -> bool:
        """Set playback volume (0-100)"""
        if not self.is_authenticated:
            return False
        
        try:
            volume = max(0, min(100, volume))
            self.sp.volume(volume)
            
            self.logger.info(f"Set Spotify volume to {volume}%")
            return True
            
        except Exception as e:
            self.logger.error(f"Error setting volume: {e}")
            return False
    
    async def get_current_playback(self) -> Optional[Dict[str, Any]]:
        """Get current playback state"""
        if not self.is_authenticated:
            return None
        
        try:
            playback = self.sp.current_playback()
            
            if playback and playback['is_playing']:
                track = playback['item']
                return {
                    'is_playing': True,
                    'track': {
                        'id': track['id'],
                        'name': track['name'],
                        'artist': track['artists'][0]['name'] if track['artists'] else 'Unknown',
                        'album': track['album']['name'],
                        'duration_ms': track['duration_ms'],
                        'progress_ms': playback.get('progress_ms', 0)
                    },
                    'volume': playback.get('device', {}).get('volume_percent', 50)
                }
            else:
                return {
                    'is_playing': False,
                    'track': None,
                    'volume': 50
                }
                
        except Exception as e:
            self.logger.error(f"Error getting current playback: {e}")
            return None
    
    async def get_recommendations(self, seed_tracks: List[str] = None, limit: int = 20) -> List[Dict[str, Any]]:
        """Get track recommendations"""
        if not self.is_authenticated:
            return []
        
        try:
            recommendations = self.sp.recommendations(
                seed_tracks=seed_tracks or [],
                limit=limit
            )
            
            tracks = []
            for track in recommendations['tracks']:
                track_info = {
                    'id': track['id'],
                    'name': track['name'],
                    'artist': track['artists'][0]['name'] if track['artists'] else 'Unknown',
                    'album': track['album']['name'],
                    'duration_ms': track['duration_ms'],
                    'uri': track['uri']
                }
                tracks.append(track_info)
            
            self.logger.info(f"Got {len(tracks)} track recommendations")
            return tracks
            
        except Exception as e:
            self.logger.error(f"Error getting recommendations: {e}")
            return []
    
    async def get_user_top_tracks(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Get user's top tracks"""
        if not self.is_authenticated:
            return []
        
        try:
            top_tracks = self.sp.current_user_top_tracks(limit=limit)
            tracks = []
            
            for track in top_tracks['items']:
                track_info = {
                    'id': track['id'],
                    'name': track['name'],
                    'artist': track['artists'][0]['name'] if track['artists'] else 'Unknown',
                    'album': track['album']['name'],
                    'duration_ms': track['duration_ms'],
                    'uri': track['uri']
                }
                tracks.append(track_info)
            
            self.logger.info(f"Got {len(tracks)} top tracks")
            return tracks
            
        except Exception as e:
            self.logger.error(f"Error getting top tracks: {e}")
            return []
    
    def is_available(self) -> bool:
        """Check if Spotify client is available"""
        return self.is_authenticated and self.sp is not None
    
    async def get_status(self) -> Dict[str, Any]:
        """Get Spotify client status"""
        return {
            'authenticated': self.is_authenticated,
            'user': self.current_user['display_name'] if self.current_user else None,
            'is_playing': self.is_playing,
            'current_track': self.current_track,
            'current_playlist': self.current_playlist
        } 