"""
Mobile API for Smart Shower
Handles communication with mobile app via REST API and WebSocket
"""

import asyncio
import json
import logging
import time
from typing import Optional, Callable, Dict, Any, List
from enum import Enum
from dataclasses import dataclass
import aiohttp
from aiohttp import web, WSMsgType


class ConnectionState(Enum):
    """Mobile connection states"""
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    AUTHENTICATED = "authenticated"


@dataclass
class MobileDevice:
    """Mobile device information"""
    device_id: str
    name: str
    platform: str  # ios, android, web
    last_seen: float
    is_authenticated: bool = False


class MobileAPI:
    """Handles mobile app communication"""
    
    def __init__(self, config):
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Connection state
        self.connection_state = ConnectionState.DISCONNECTED
        self.connected_devices: List[MobileDevice] = []
        self.active_connections: Dict[str, web.WebSocketResponse] = {}
        
        # API settings
        self.api_host = "0.0.0.0"
        self.api_port = 8080
        self.websocket_port = 8081
        
        # Authentication
        self.auth_tokens: Dict[str, str] = {}
        self.session_timeout = 3600  # 1 hour
        
        # Event callbacks
        self.on_shower_start_request: Optional[Callable] = None
        self.on_shower_stop_request: Optional[Callable] = None
        self.on_audio_control_request: Optional[Callable] = None
        self.on_temperature_change_request: Optional[Callable] = None
        self.on_device_connected: Optional[Callable] = None
        self.on_device_disconnected: Optional[Callable] = None
        
        # Web server
        self.web_app = None
        self.web_runner = None
        self.websocket_app = None
        self.websocket_runner = None
        
        # Control loop
        self.control_task = None
        self.is_running = False
        
    async def initialize(self):
        """Initialize the mobile API"""
        self.logger.info("Initializing mobile API...")
        
        # Load API settings
        await self._load_api_settings()
        
        # Initialize web server
        await self._initialize_web_server()
        
        # Initialize WebSocket server
        await self._initialize_websocket_server()
        
        self.logger.info("Mobile API initialized")
    
    async def _load_api_settings(self):
        """Load API settings from config"""
        settings = self.config.get('mobile_api', {})
        self.api_host = settings.get('host', '0.0.0.0')
        self.api_port = settings.get('port', 8080)
        self.websocket_port = settings.get('websocket_port', 8081)
        self.session_timeout = settings.get('session_timeout', 3600)
        
        self.logger.info(f"Loaded API settings - Host: {self.api_host}:{self.api_port}")
    
    async def _initialize_web_server(self):
        """Initialize REST API web server"""
        self.web_app = web.Application()
        
        # Add routes
        self.web_app.router.add_get('/', self._handle_root)
        self.web_app.router.add_get('/api/status', self._handle_status)
        self.web_app.router.add_post('/api/shower/start', self._handle_shower_start)
        self.web_app.router.add_post('/api/shower/stop', self._handle_shower_stop)
        self.web_app.router.add_get('/api/shower/status', self._handle_shower_status)
        self.web_app.router.add_put('/api/shower/temperature', self._handle_temperature_change)
        self.web_app.router.add_post('/api/audio/play', self._handle_audio_play)
        self.web_app.router.add_post('/api/audio/pause', self._handle_audio_pause)
        self.web_app.router.add_post('/api/audio/resume', self._handle_audio_resume)
        self.web_app.router.add_post('/api/audio/stop', self._handle_audio_stop)
        self.web_app.router.add_put('/api/audio/volume', self._handle_volume_change)
        self.web_app.router.add_get('/api/safety/status', self._handle_safety_status)
        self.web_app.router.add_post('/api/safety/emergency_stop', self._handle_emergency_stop)
        self.web_app.router.add_get('/api/audio/search', self._handle_audio_search)
        self.web_app.router.add_get('/api/audio/tracks', self._handle_audio_tracks)
        
        # Add middleware for CORS
        self.web_app.middlewares.append(self._cors_middleware)
        
        self.logger.info("REST API server initialized")
    
    async def _initialize_websocket_server(self):
        """Initialize WebSocket server for real-time communication"""
        self.websocket_app = web.Application()
        
        # Add WebSocket route
        self.websocket_app.router.add_get('/ws', self._handle_websocket)
        
        self.logger.info("WebSocket server initialized")
    
    async def _cors_middleware(self, request, handler):
        """CORS middleware for cross-origin requests"""
        response = await handler(request)
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
        return response
    
    async def start(self):
        """Start the mobile API"""
        self.logger.info("Starting mobile API...")
        self.is_running = True
        
        # Start web servers
        self.web_runner = web.AppRunner(self.web_app)
        await self.web_runner.setup()
        self.web_site = web.TCPSite(self.web_runner, self.api_host, self.api_port)
        await self.web_site.start()
        
        self.websocket_runner = web.AppRunner(self.websocket_app)
        await self.websocket_runner.setup()
        self.websocket_site = web.TCPSite(self.websocket_runner, self.api_host, self.websocket_port)
        await self.websocket_site.start()
        
        # Start control loop
        self.control_task = asyncio.create_task(self._control_loop())
        
        self.logger.info(f"Mobile API started - REST: http://{self.api_host}:{self.api_port}, WebSocket: ws://{self.api_host}:{self.websocket_port}")
    
    async def shutdown(self):
        """Shutdown the mobile API"""
        self.logger.info("Shutting down mobile API...")
        self.is_running = False
        
        # Close all WebSocket connections
        for ws in self.active_connections.values():
            await ws.close()
        self.active_connections.clear()
        
        # Stop web servers
        if self.web_runner:
            await self.web_runner.cleanup()
        if self.websocket_runner:
            await self.websocket_runner.cleanup()
        
        # Cancel control task
        if self.control_task:
            self.control_task.cancel()
            try:
                await self.control_task
            except asyncio.CancelledError:
                pass
        
        self.logger.info("Mobile API shutdown complete")
    
    # REST API handlers
    async def _handle_root(self, request):
        """Handle root endpoint"""
        return web.json_response({
            'name': 'Smart Shower OS',
            'version': '1.0.0',
            'status': 'running'
        })
    
    async def _handle_status(self, request):
        """Handle status endpoint"""
        return web.json_response({
            'connection_state': self.connection_state.value,
            'connected_devices': len(self.connected_devices),
            'active_connections': len(self.active_connections),
            'uptime': time.time() - (getattr(self, '_start_time', time.time()))
        })
    
    async def _handle_shower_start(self, request):
        """Handle shower start request"""
        try:
            data = await request.json()
            temperature = data.get('temperature', 38.0)
            audio_source = data.get('audio_source')
            
            self.logger.info(f"Mobile shower start request - Temp: {temperature}°C, Audio: {audio_source}")
            
            # Trigger event
            if self.on_shower_start_request:
                await self.on_shower_start_request({
                    'temperature': temperature,
                    'audio_source': audio_source
                })
            
            return web.json_response({'status': 'success', 'message': 'Shower started'})
            
        except Exception as e:
            self.logger.error(f"Error handling shower start: {e}")
            return web.json_response({'status': 'error', 'message': str(e)}, status=500)
    
    async def _handle_shower_stop(self, request):
        """Handle shower stop request"""
        try:
            self.logger.info("Mobile shower stop request")
            
            # Trigger event
            if self.on_shower_stop_request:
                await self.on_shower_stop_request()
            
            return web.json_response({'status': 'success', 'message': 'Shower stopped'})
            
        except Exception as e:
            self.logger.error(f"Error handling shower stop: {e}")
            return web.json_response({'status': 'error', 'message': str(e)}, status=500)
    
    async def _handle_shower_status(self, request):
        """Handle shower status request"""
        try:
            # This would get status from water controller
            status = {
                'active': False,
                'temperature': 38.0,
                'flow_rate': 0.0,
                'duration': 0
            }
            
            return web.json_response(status)
            
        except Exception as e:
            self.logger.error(f"Error handling shower status: {e}")
            return web.json_response({'status': 'error', 'message': str(e)}, status=500)
    
    async def _handle_temperature_change(self, request):
        """Handle temperature change request"""
        try:
            data = await request.json()
            temperature = data.get('temperature', 38.0)
            
            self.logger.info(f"Mobile temperature change request: {temperature}°C")
            
            # Trigger event
            if self.on_temperature_change_request:
                await self.on_temperature_change_request(temperature)
            
            return web.json_response({'status': 'success', 'temperature': temperature})
            
        except Exception as e:
            self.logger.error(f"Error handling temperature change: {e}")
            return web.json_response({'status': 'error', 'message': str(e)}, status=500)
    
    async def _handle_audio_play(self, request):
        """Handle audio play request"""
        try:
            data = await request.json()
            source = data.get('source')
            
            self.logger.info(f"Mobile audio play request: {source}")
            
            # Trigger event
            if self.on_audio_control_request:
                await self.on_audio_control_request({
                    'action': 'play',
                    'source': source
                })
            
            return web.json_response({'status': 'success', 'message': 'Audio started'})
            
        except Exception as e:
            self.logger.error(f"Error handling audio play: {e}")
            return web.json_response({'status': 'error', 'message': str(e)}, status=500)
    
    async def _handle_audio_pause(self, request):
        """Handle audio pause request"""
        try:
            self.logger.info("Mobile audio pause request")
            
            # Trigger event
            if self.on_audio_control_request:
                await self.on_audio_control_request({'action': 'pause'})
            
            return web.json_response({'status': 'success', 'message': 'Audio paused'})
            
        except Exception as e:
            self.logger.error(f"Error handling audio pause: {e}")
            return web.json_response({'status': 'error', 'message': str(e)}, status=500)
    
    async def _handle_audio_resume(self, request):
        """Handle audio resume request"""
        try:
            self.logger.info("Mobile audio resume request")
            
            # Trigger event
            if self.on_audio_control_request:
                await self.on_audio_control_request({'action': 'resume'})
            
            return web.json_response({'status': 'success', 'message': 'Audio resumed'})
            
        except Exception as e:
            self.logger.error(f"Error handling audio resume: {e}")
            return web.json_response({'status': 'error', 'message': str(e)}, status=500)
    
    async def _handle_audio_stop(self, request):
        """Handle audio stop request"""
        try:
            self.logger.info("Mobile audio stop request")
            
            # Trigger event
            if self.on_audio_control_request:
                await self.on_audio_control_request({'action': 'stop'})
            
            return web.json_response({'status': 'success', 'message': 'Audio stopped'})
            
        except Exception as e:
            self.logger.error(f"Error handling audio stop: {e}")
            return web.json_response({'status': 'error', 'message': str(e)}, status=500)
    
    async def _handle_volume_change(self, request):
        """Handle volume change request"""
        try:
            data = await request.json()
            volume = data.get('volume', 50)
            
            self.logger.info(f"Mobile volume change request: {volume}%")
            
            # Trigger event
            if self.on_audio_control_request:
                await self.on_audio_control_request({
                    'action': 'volume',
                    'volume': volume
                })
            
            return web.json_response({'status': 'success', 'volume': volume})
            
        except Exception as e:
            self.logger.error(f"Error handling volume change: {e}")
            return web.json_response({'status': 'error', 'message': str(e)}, status=500)
    
    async def _handle_safety_status(self, request):
        """Handle safety status request"""
        try:
            # This would get status from safety monitor
            status = {
                'safety_state': 'safe',
                'door_state': 'closed',
                'leak_detected': False,
                'emergency_stop_active': False
            }
            
            return web.json_response(status)
            
        except Exception as e:
            self.logger.error(f"Error handling safety status: {e}")
            return web.json_response({'status': 'error', 'message': str(e)}, status=500)
    
    async def _handle_emergency_stop(self, request):
        """Handle emergency stop request"""
        try:
            self.logger.warning("Mobile emergency stop request")
            
            # This would trigger emergency stop
            return web.json_response({'status': 'success', 'message': 'Emergency stop activated'})
            
        except Exception as e:
            self.logger.error(f"Error handling emergency stop: {e}")
            return web.json_response({'status': 'error', 'message': str(e)}, status=500)
    
    async def _handle_audio_search(self, request):
        """Handle audio search request"""
        try:
            query = request.query.get('q', '')
            source = request.query.get('source', 'spotify')
            
            self.logger.info(f"Mobile audio search request: {query} ({source})")
            
            # This would search the specified audio source
            results = []
            
            return web.json_response({'status': 'success', 'results': results})
            
        except Exception as e:
            self.logger.error(f"Error handling audio search: {e}")
            return web.json_response({'status': 'error', 'message': str(e)}, status=500)
    
    async def _handle_audio_tracks(self, request):
        """Handle audio tracks request"""
        try:
            source = request.query.get('source', 'local')
            
            self.logger.info(f"Mobile audio tracks request: {source}")
            
            # This would get tracks from the specified source
            tracks = []
            
            return web.json_response({'status': 'success', 'tracks': tracks})
            
        except Exception as e:
            self.logger.error(f"Error handling audio tracks: {e}")
            return web.json_response({'status': 'error', 'message': str(e)}, status=500)
    
    # WebSocket handlers
    async def _handle_websocket(self, request):
        """Handle WebSocket connection"""
        ws = web.WebSocketResponse()
        await ws.prepare(request)
        
        device_id = request.query.get('device_id', f'device_{int(time.time())}')
        device_name = request.query.get('name', 'Unknown Device')
        platform = request.query.get('platform', 'web')
        
        self.logger.info(f"WebSocket connection from {device_name} ({platform})")
        
        # Register device
        device = MobileDevice(
            device_id=device_id,
            name=device_name,
            platform=platform,
            last_seen=time.time()
        )
        self.connected_devices.append(device)
        self.active_connections[device_id] = ws
        
        # Update connection state
        self.connection_state = ConnectionState.CONNECTED
        
        # Trigger device connected event
        if self.on_device_connected:
            await self.on_device_connected(device)
        
        try:
            async for msg in ws:
                if msg.type == WSMsgType.TEXT:
                    await self._handle_websocket_message(device_id, msg.data)
                elif msg.type == WSMsgType.ERROR:
                    self.logger.error(f"WebSocket error: {ws.exception()}")
                    break
        except Exception as e:
            self.logger.error(f"WebSocket error: {e}")
        finally:
            # Clean up connection
            if device_id in self.active_connections:
                del self.active_connections[device_id]
            
            # Remove device
            self.connected_devices = [d for d in self.connected_devices if d.device_id != device_id]
            
            # Update connection state
            if not self.active_connections:
                self.connection_state = ConnectionState.DISCONNECTED
            
            # Trigger device disconnected event
            if self.on_device_disconnected:
                await self.on_device_disconnected(device)
            
            self.logger.info(f"WebSocket connection closed for {device_name}")
        
        return ws
    
    async def _handle_websocket_message(self, device_id: str, message: str):
        """Handle WebSocket message"""
        try:
            data = json.loads(message)
            message_type = data.get('type')
            
            self.logger.debug(f"WebSocket message from {device_id}: {message_type}")
            
            if message_type == 'shower_start':
                await self._handle_ws_shower_start(device_id, data)
            elif message_type == 'shower_stop':
                await self._handle_ws_shower_stop(device_id, data)
            elif message_type == 'audio_control':
                await self._handle_ws_audio_control(device_id, data)
            elif message_type == 'temperature_change':
                await self._handle_ws_temperature_change(device_id, data)
            elif message_type == 'ping':
                await self._send_websocket_message(device_id, {'type': 'pong'})
            else:
                self.logger.warning(f"Unknown WebSocket message type: {message_type}")
                
        except json.JSONDecodeError:
            self.logger.error(f"Invalid JSON in WebSocket message: {message}")
        except Exception as e:
            self.logger.error(f"Error handling WebSocket message: {e}")
    
    async def _handle_ws_shower_start(self, device_id: str, data: Dict[str, Any]):
        """Handle WebSocket shower start message"""
        temperature = data.get('temperature', 38.0)
        audio_source = data.get('audio_source')
        
        self.logger.info(f"WebSocket shower start from {device_id}: {temperature}°C")
        
        if self.on_shower_start_request:
            await self.on_shower_start_request({
                'temperature': temperature,
                'audio_source': audio_source
            })
    
    async def _handle_ws_shower_stop(self, device_id: str, data: Dict[str, Any]):
        """Handle WebSocket shower stop message"""
        self.logger.info(f"WebSocket shower stop from {device_id}")
        
        if self.on_shower_stop_request:
            await self.on_shower_stop_request()
    
    async def _handle_ws_audio_control(self, device_id: str, data: Dict[str, Any]):
        """Handle WebSocket audio control message"""
        action = data.get('action')
        
        self.logger.info(f"WebSocket audio control from {device_id}: {action}")
        
        if self.on_audio_control_request:
            await self.on_audio_control_request(data)
    
    async def _handle_ws_temperature_change(self, device_id: str, data: Dict[str, Any]):
        """Handle WebSocket temperature change message"""
        temperature = data.get('temperature', 38.0)
        
        self.logger.info(f"WebSocket temperature change from {device_id}: {temperature}°C")
        
        if self.on_temperature_change_request:
            await self.on_temperature_change_request(temperature)
    
    async def _send_websocket_message(self, device_id: str, message: Dict[str, Any]):
        """Send message to specific device via WebSocket"""
        if device_id in self.active_connections:
            ws = self.active_connections[device_id]
            try:
                await ws.send_str(json.dumps(message))
            except Exception as e:
                self.logger.error(f"Error sending WebSocket message: {e}")
    
    async def broadcast_message(self, message: Dict[str, Any]):
        """Broadcast message to all connected devices"""
        for device_id in list(self.active_connections.keys()):
            await self._send_websocket_message(device_id, message)
    
    async def send_emergency_notification(self, message: str):
        """Send emergency notification to all devices"""
        await self.broadcast_message({
            'type': 'emergency_notification',
            'message': message,
            'timestamp': time.time()
        })
    
    async def send_status_update(self, status: Dict[str, Any]):
        """Send status update to all devices"""
        await self.broadcast_message({
            'type': 'status_update',
            'status': status,
            'timestamp': time.time()
        })
    
    async def _control_loop(self):
        """Main control loop for mobile API"""
        while self.is_running:
            try:
                # Clean up expired sessions
                await self._cleanup_expired_sessions()
                
                # Update device last seen times
                await self._update_device_timestamps()
                
                await asyncio.sleep(1)  # 1 second control loop
                
            except Exception as e:
                self.logger.error(f"Error in mobile API control loop: {e}")
                await asyncio.sleep(5)
    
    async def _cleanup_expired_sessions(self):
        """Clean up expired authentication sessions"""
        current_time = time.time()
        expired_tokens = []
        
        for token, timestamp in self.auth_tokens.items():
            if current_time - timestamp > self.session_timeout:
                expired_tokens.append(token)
        
        for token in expired_tokens:
            del self.auth_tokens[token]
        
        if expired_tokens:
            self.logger.info(f"Cleaned up {len(expired_tokens)} expired sessions")
    
    async def _update_device_timestamps(self):
        """Update device last seen timestamps"""
        current_time = time.time()
        
        for device in self.connected_devices:
            if device.device_id in self.active_connections:
                device.last_seen = current_time
    
    async def get_connection_stats(self):
        """Get connection statistics"""
        return {
            'total_connections': len(self.active_connections),
            'connected_devices': len(self.connected_devices),
            'connection_state': self.connection_state.value,
            'devices': [
                {
                    'id': device.device_id,
                    'name': device.name,
                    'platform': device.platform,
                    'last_seen': device.last_seen
                }
                for device in self.connected_devices
            ]
        } 