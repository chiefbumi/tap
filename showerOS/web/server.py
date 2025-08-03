"""
Web Server for Smart Shower OS
Provides web interface for system control
"""

import asyncio
import logging
import os
from pathlib import Path
from typing import Dict, Any
from aiohttp import web, WSMsgType
import aiohttp_cors


class WebServer:
    """Web server for smart shower interface"""
    
    def __init__(self, config):
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Web server settings
        self.host = config.get('web.host', '0.0.0.0')
        self.port = config.get('web.port', 8082)
        self.static_path = config.get('web.static_path', './web/static')
        self.template_path = config.get('web.template_path', './web/templates')
        
        # Web application
        self.app = None
        self.runner = None
        self.site = None
        
        # WebSocket connections
        self.websocket_connections = []
        
        # System reference (will be set by main system)
        self.system = None
        
    async def initialize(self):
        """Initialize the web server"""
        self.logger.info("Initializing web server...")
        
        # Create web application
        self.app = web.Application()
        
        # Set up CORS
        cors = aiohttp_cors.setup(self.app, defaults={
            "*": aiohttp_cors.ResourceOptions(
                allow_credentials=True,
                expose_headers="*",
                allow_headers="*",
                allow_methods="*"
            )
        })
        
        # Add routes
        await self._setup_routes()
        
        # Add CORS to all routes
        for route in list(self.app.router.routes()):
            cors.add(route)
        
        self.logger.info("Web server initialized")
    
    async def _setup_routes(self):
        """Set up web server routes"""
        # Static files
        static_path = Path(self.static_path)
        if static_path.exists():
            self.app.router.add_static('/static', static_path)
        
        # Main pages
        self.app.router.add_get('/', self._handle_dashboard)
        self.app.router.add_get('/dashboard', self._handle_dashboard)
        self.app.router.add_get('/mobile', self._handle_mobile_app)
        self.app.router.add_get('/settings', self._handle_settings)
        
        # API endpoints
        self.app.router.add_get('/api/status', self._handle_api_status)
        self.app.router.add_get('/api/system', self._handle_api_system)
        self.app.router.add_post('/api/shower/start', self._handle_api_shower_start)
        self.app.router.add_post('/api/shower/stop', self._handle_api_shower_stop)
        self.app.router.add_get('/api/shower/status', self._handle_api_shower_status)
        self.app.router.add_put('/api/shower/temperature', self._handle_api_temperature)
        self.app.router.add_post('/api/audio/play', self._handle_api_audio_play)
        self.app.router.add_post('/api/audio/pause', self._handle_api_audio_pause)
        self.app.router.add_post('/api/audio/resume', self._handle_api_audio_resume)
        self.app.router.add_post('/api/audio/stop', self._handle_api_audio_stop)
        self.app.router.add_put('/api/audio/volume', self._handle_api_volume)
        self.app.router.add_get('/api/safety/status', self._handle_api_safety_status)
        self.app.router.add_post('/api/safety/emergency_stop', self._handle_api_emergency_stop)
        
        # WebSocket
        self.app.router.add_get('/ws', self._handle_websocket)
        
        self.logger.info("Web routes configured")
    
    async def start(self):
        """Start the web server"""
        self.logger.info("Starting web server...")
        
        # Create runner
        self.runner = web.AppRunner(self.app)
        await self.runner.setup()
        
        # Create site
        self.site = web.TCPSite(self.runner, self.host, self.port)
        await self.site.start()
        
        self.logger.info(f"Web server started at http://{self.host}:{self.port}")
    
    async def shutdown(self):
        """Shutdown the web server"""
        self.logger.info("Shutting down web server...")
        
        # Close WebSocket connections
        for ws in self.websocket_connections:
            await ws.close()
        self.websocket_connections.clear()
        
        # Stop site and runner
        if self.site:
            await self.site.stop()
        if self.runner:
            await self.runner.cleanup()
        
        self.logger.info("Web server shutdown complete")
    
    # Page handlers
    async def _handle_dashboard(self, request):
        """Handle dashboard page"""
        html = await self._get_dashboard_html()
        return web.Response(text=html, content_type='text/html')
    
    async def _handle_mobile_app(self, request):
        """Handle mobile app page"""
        html = await self._get_mobile_app_html()
        return web.Response(text=html, content_type='text/html')
    
    async def _handle_settings(self, request):
        """Handle settings page"""
        html = await self._get_settings_html()
        return web.Response(text=html, content_type='text/html')
    
    # API handlers
    async def _handle_api_status(self, request):
        """Handle API status endpoint"""
        if not self.system:
            return web.json_response({'error': 'System not available'}, status=503)
        
        status = {
            'system': await self.system.get_status(),
            'water': await self.system.water_controller.get_status() if self.system.water_controller else None,
            'audio': await self.system.audio_manager.get_status() if self.system.audio_manager else None,
            'safety': await self.system.safety_monitor.get_status() if self.system.safety_monitor else None,
            'mobile': await self.system.mobile_api.get_connection_stats() if self.system.mobile_api else None
        }
        
        return web.json_response(status)
    
    async def _handle_api_system(self, request):
        """Handle system info endpoint"""
        if not self.system:
            return web.json_response({'error': 'System not available'}, status=503)
        
        system_info = {
            'name': 'Smart Shower OS',
            'version': '1.0.0',
            'uptime': 0,  # Would calculate actual uptime
            'status': 'running'
        }
        
        return web.json_response(system_info)
    
    async def _handle_api_shower_start(self, request):
        """Handle shower start API"""
        if not self.system:
            return web.json_response({'error': 'System not available'}, status=503)
        
        try:
            data = await request.json()
            temperature = data.get('temperature', 38.0)
            audio_source = data.get('audio_source')
            
            await self.system.start_shower(temperature, audio_source)
            
            return web.json_response({'status': 'success', 'message': 'Shower started'})
            
        except Exception as e:
            self.logger.error(f"Error starting shower: {e}")
            return web.json_response({'error': str(e)}, status=500)
    
    async def _handle_api_shower_stop(self, request):
        """Handle shower stop API"""
        if not self.system:
            return web.json_response({'error': 'System not available'}, status=503)
        
        try:
            await self.system.stop_shower()
            
            return web.json_response({'status': 'success', 'message': 'Shower stopped'})
            
        except Exception as e:
            self.logger.error(f"Error stopping shower: {e}")
            return web.json_response({'error': str(e)}, status=500)
    
    async def _handle_api_shower_status(self, request):
        """Handle shower status API"""
        if not self.system or not self.system.water_controller:
            return web.json_response({'error': 'Water controller not available'}, status=503)
        
        try:
            status = await self.system.water_controller.get_status()
            return web.json_response(status)
            
        except Exception as e:
            self.logger.error(f"Error getting shower status: {e}")
            return web.json_response({'error': str(e)}, status=500)
    
    async def _handle_api_temperature(self, request):
        """Handle temperature change API"""
        if not self.system or not self.system.water_controller:
            return web.json_response({'error': 'Water controller not available'}, status=503)
        
        try:
            data = await request.json()
            temperature = data.get('temperature', 38.0)
            
            await self.system.water_controller.set_temperature(temperature)
            
            return web.json_response({'status': 'success', 'temperature': temperature})
            
        except Exception as e:
            self.logger.error(f"Error setting temperature: {e}")
            return web.json_response({'error': str(e)}, status=500)
    
    async def _handle_api_audio_play(self, request):
        """Handle audio play API"""
        if not self.system or not self.system.audio_manager:
            return web.json_response({'error': 'Audio manager not available'}, status=503)
        
        try:
            data = await request.json()
            source = data.get('source')
            
            await self.system.audio_manager.start_playback(source)
            
            return web.json_response({'status': 'success', 'message': 'Audio started'})
            
        except Exception as e:
            self.logger.error(f"Error starting audio: {e}")
            return web.json_response({'error': str(e)}, status=500)
    
    async def _handle_api_audio_pause(self, request):
        """Handle audio pause API"""
        if not self.system or not self.system.audio_manager:
            return web.json_response({'error': 'Audio manager not available'}, status=503)
        
        try:
            await self.system.audio_manager.pause_playback()
            
            return web.json_response({'status': 'success', 'message': 'Audio paused'})
            
        except Exception as e:
            self.logger.error(f"Error pausing audio: {e}")
            return web.json_response({'error': str(e)}, status=500)
    
    async def _handle_api_audio_resume(self, request):
        """Handle audio resume API"""
        if not self.system or not self.system.audio_manager:
            return web.json_response({'error': 'Audio manager not available'}, status=503)
        
        try:
            await self.system.audio_manager.resume_playback()
            
            return web.json_response({'status': 'success', 'message': 'Audio resumed'})
            
        except Exception as e:
            self.logger.error(f"Error resuming audio: {e}")
            return web.json_response({'error': str(e)}, status=500)
    
    async def _handle_api_audio_stop(self, request):
        """Handle audio stop API"""
        if not self.system or not self.system.audio_manager:
            return web.json_response({'error': 'Audio manager not available'}, status=503)
        
        try:
            await self.system.audio_manager.stop_playback()
            
            return web.json_response({'status': 'success', 'message': 'Audio stopped'})
            
        except Exception as e:
            self.logger.error(f"Error stopping audio: {e}")
            return web.json_response({'error': str(e)}, status=500)
    
    async def _handle_api_volume(self, request):
        """Handle volume change API"""
        if not self.system or not self.system.audio_manager:
            return web.json_response({'error': 'Audio manager not available'}, status=503)
        
        try:
            data = await request.json()
            volume = data.get('volume', 50)
            
            await self.system.audio_manager.set_volume(volume)
            
            return web.json_response({'status': 'success', 'volume': volume})
            
        except Exception as e:
            self.logger.error(f"Error setting volume: {e}")
            return web.json_response({'error': str(e)}, status=500)
    
    async def _handle_api_safety_status(self, request):
        """Handle safety status API"""
        if not self.system or not self.system.safety_monitor:
            return web.json_response({'error': 'Safety monitor not available'}, status=503)
        
        try:
            status = await self.system.safety_monitor.get_status()
            return web.json_response(status)
            
        except Exception as e:
            self.logger.error(f"Error getting safety status: {e}")
            return web.json_response({'error': str(e)}, status=500)
    
    async def _handle_api_emergency_stop(self, request):
        """Handle emergency stop API"""
        if not self.system or not self.system.safety_monitor:
            return web.json_response({'error': 'Safety monitor not available'}, status=503)
        
        try:
            await self.system.safety_monitor.emergency_stop("Web interface emergency stop")
            
            return web.json_response({'status': 'success', 'message': 'Emergency stop activated'})
            
        except Exception as e:
            self.logger.error(f"Error emergency stop: {e}")
            return web.json_response({'error': str(e)}, status=500)
    
    # WebSocket handler
    async def _handle_websocket(self, request):
        """Handle WebSocket connection"""
        ws = web.WebSocketResponse()
        await ws.prepare(request)
        
        self.websocket_connections.append(ws)
        self.logger.info("WebSocket connection established")
        
        try:
            async for msg in ws:
                if msg.type == WSMsgType.TEXT:
                    await self._handle_websocket_message(ws, msg.data)
                elif msg.type == WSMsgType.ERROR:
                    self.logger.error(f"WebSocket error: {ws.exception()}")
                    break
        except Exception as e:
            self.logger.error(f"WebSocket error: {e}")
        finally:
            if ws in self.websocket_connections:
                self.websocket_connections.remove(ws)
            self.logger.info("WebSocket connection closed")
        
        return ws
    
    async def _handle_websocket_message(self, ws, message):
        """Handle WebSocket message"""
        try:
            import json
            data = json.loads(message)
            message_type = data.get('type')
            
            self.logger.debug(f"WebSocket message: {message_type}")
            
            if message_type == 'get_status':
                # Send current status
                if self.system:
                    status = await self.system.get_status()
                    await ws.send_str(json.dumps({
                        'type': 'status_update',
                        'data': status
                    }))
            
            elif message_type == 'shower_start':
                # Start shower
                if self.system:
                    temperature = data.get('temperature', 38.0)
                    audio_source = data.get('audio_source')
                    await self.system.start_shower(temperature, audio_source)
            
            elif message_type == 'shower_stop':
                # Stop shower
                if self.system:
                    await self.system.stop_shower()
            
            elif message_type == 'audio_control':
                # Control audio
                if self.system and self.system.audio_manager:
                    action = data.get('action')
                    if action == 'play':
                        await self.system.audio_manager.start_playback(data.get('source'))
                    elif action == 'pause':
                        await self.system.audio_manager.pause_playback()
                    elif action == 'resume':
                        await self.system.audio_manager.resume_playback()
                    elif action == 'stop':
                        await self.system.audio_manager.stop_playback()
                    elif action == 'volume':
                        await self.system.audio_manager.set_volume(data.get('volume', 50))
            
            elif message_type == 'ping':
                # Respond to ping
                await ws.send_str(json.dumps({'type': 'pong'}))
            
        except json.JSONDecodeError:
            self.logger.error(f"Invalid JSON in WebSocket message: {message}")
        except Exception as e:
            self.logger.error(f"Error handling WebSocket message: {e}")
    
    # HTML template methods
    async def _get_dashboard_html(self) -> str:
        """Get dashboard HTML"""
        return """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Smart Shower OS - Dashboard</title>
    <style>
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 0;
            padding: 20px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
        }
        .header {
            text-align: center;
            margin-bottom: 30px;
        }
        .status-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        .status-card {
            background: rgba(255, 255, 255, 0.1);
            border-radius: 10px;
            padding: 20px;
            backdrop-filter: blur(10px);
        }
        .control-panel {
            background: rgba(255, 255, 255, 0.1);
            border-radius: 10px;
            padding: 20px;
            backdrop-filter: blur(10px);
        }
        .button {
            background: #4CAF50;
            color: white;
            border: none;
            padding: 10px 20px;
            border-radius: 5px;
            cursor: pointer;
            margin: 5px;
        }
        .button:hover {
            background: #45a049;
        }
        .button.danger {
            background: #f44336;
        }
        .button.danger:hover {
            background: #da190b;
        }
        .slider {
            width: 100%;
            margin: 10px 0;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🚿 Smart Shower OS</h1>
            <p>Control your smart shower from anywhere</p>
        </div>
        
        <div class="status-grid">
            <div class="status-card">
                <h3>Water Status</h3>
                <div id="water-status">Loading...</div>
            </div>
            
            <div class="status-card">
                <h3>Audio Status</h3>
                <div id="audio-status">Loading...</div>
            </div>
            
            <div class="status-card">
                <h3>Safety Status</h3>
                <div id="safety-status">Loading...</div>
            </div>
        </div>
        
        <div class="control-panel">
            <h3>Controls</h3>
            <button class="button" onclick="startShower()">Start Shower</button>
            <button class="button danger" onclick="stopShower()">Stop Shower</button>
            <button class="button danger" onclick="emergencyStop()">Emergency Stop</button>
            
            <h4>Temperature Control</h4>
            <input type="range" min="20" max="45" value="38" class="slider" id="temp-slider">
            <span id="temp-value">38°C</span>
            
            <h4>Audio Control</h4>
            <button class="button" onclick="playAudio()">Play Audio</button>
            <button class="button" onclick="pauseAudio()">Pause Audio</button>
            <button class="button" onclick="stopAudio()">Stop Audio</button>
            
            <h4>Volume</h4>
            <input type="range" min="0" max="100" value="50" class="slider" id="volume-slider">
            <span id="volume-value">50%</span>
        </div>
    </div>
    
    <script>
        // WebSocket connection
        let ws = null;
        
        function connectWebSocket() {
            ws = new WebSocket(`ws://${window.location.host}/ws`);
            
            ws.onopen = function() {
                console.log('WebSocket connected');
                requestStatus();
            };
            
            ws.onmessage = function(event) {
                const data = JSON.parse(event.data);
                if (data.type === 'status_update') {
                    updateStatus(data.data);
                }
            };
            
            ws.onclose = function() {
                console.log('WebSocket disconnected');
                setTimeout(connectWebSocket, 5000);
            };
        }
        
        function requestStatus() {
            if (ws && ws.readyState === WebSocket.OPEN) {
                ws.send(JSON.stringify({type: 'get_status'}));
            }
        }
        
        function updateStatus(status) {
            // Update water status
            if (status.water) {
                document.getElementById('water-status').innerHTML = `
                    <p>Temperature: ${status.water.temperature.current}°C</p>
                    <p>Flow Rate: ${status.water.flow.rate} L/min</p>
                    <p>State: ${status.water.flow.state}</p>
                `;
            }
            
            // Update audio status
            if (status.audio) {
                document.getElementById('audio-status').innerHTML = `
                    <p>State: ${status.audio.playback_state}</p>
                    <p>Volume: ${status.audio.volume}%</p>
                    <p>Track: ${status.audio.current_track ? status.audio.current_track.title : 'None'}</p>
                `;
            }
            
            // Update safety status
            if (status.safety) {
                document.getElementById('safety-status').innerHTML = `
                    <p>State: ${status.safety.safety_state}</p>
                    <p>Door: ${status.safety.door_state}</p>
                    <p>Leak: ${status.safety.leak_detected ? 'Yes' : 'No'}</p>
                `;
            }
        }
        
        // Control functions
        function startShower() {
            const temp = document.getElementById('temp-slider').value;
            fetch('/api/shower/start', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({temperature: parseFloat(temp)})
            });
        }
        
        function stopShower() {
            fetch('/api/shower/stop', {method: 'POST'});
        }
        
        function emergencyStop() {
            fetch('/api/safety/emergency_stop', {method: 'POST'});
        }
        
        function playAudio() {
            fetch('/api/audio/play', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({source: 'spotify:track:example'})
            });
        }
        
        function pauseAudio() {
            fetch('/api/audio/pause', {method: 'POST'});
        }
        
        function stopAudio() {
            fetch('/api/audio/stop', {method: 'POST'});
        }
        
        // Event listeners
        document.getElementById('temp-slider').addEventListener('input', function() {
            document.getElementById('temp-value').textContent = this.value + '°C';
        });
        
        document.getElementById('volume-slider').addEventListener('input', function() {
            document.getElementById('volume-value').textContent = this.value + '%';
            fetch('/api/audio/volume', {
                method: 'PUT',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({volume: parseInt(this.value)})
            });
        });
        
        // Initialize
        connectWebSocket();
        setInterval(requestStatus, 5000);
    </script>
</body>
</html>
        """
    
    async def _get_mobile_app_html(self) -> str:
        """Get mobile app HTML"""
        return """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Smart Shower - Mobile</title>
    <style>
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 0;
            padding: 10px;
            background: #f0f0f0;
        }
        .mobile-container {
            max-width: 400px;
            margin: 0 auto;
            background: white;
            border-radius: 15px;
            overflow: hidden;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        }
        .header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px;
            text-align: center;
        }
        .control-section {
            padding: 20px;
        }
        .button {
            width: 100%;
            background: #4CAF50;
            color: white;
            border: none;
            padding: 15px;
            border-radius: 8px;
            margin: 5px 0;
            font-size: 16px;
        }
        .button.danger {
            background: #f44336;
        }
        .slider-container {
            margin: 15px 0;
        }
        .slider {
            width: 100%;
        }
    </style>
</head>
<body>
    <div class="mobile-container">
        <div class="header">
            <h1>🚿 Smart Shower</h1>
        </div>
        
        <div class="control-section">
            <button class="button" onclick="startShower()">Start Shower</button>
            <button class="button danger" onclick="stopShower()">Stop Shower</button>
            
            <div class="slider-container">
                <label>Temperature: <span id="temp-value">38°C</span></label>
                <input type="range" min="20" max="45" value="38" class="slider" id="temp-slider">
            </div>
            
            <div class="slider-container">
                <label>Volume: <span id="volume-value">50%</span></label>
                <input type="range" min="0" max="100" value="50" class="slider" id="volume-slider">
            </div>
            
            <button class="button" onclick="playAudio()">Play Music</button>
            <button class="button" onclick="pauseAudio()">Pause Music</button>
            
            <button class="button danger" onclick="emergencyStop()">Emergency Stop</button>
        </div>
    </div>
    
    <script>
        // Mobile app functionality
        function startShower() {
            const temp = document.getElementById('temp-slider').value;
            fetch('/api/shower/start', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({temperature: parseFloat(temp)})
            });
        }
        
        function stopShower() {
            fetch('/api/shower/stop', {method: 'POST'});
        }
        
        function emergencyStop() {
            fetch('/api/safety/emergency_stop', {method: 'POST'});
        }
        
        function playAudio() {
            fetch('/api/audio/play', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({source: 'spotify:track:example'})
            });
        }
        
        function pauseAudio() {
            fetch('/api/audio/pause', {method: 'POST'});
        }
        
        // Event listeners
        document.getElementById('temp-slider').addEventListener('input', function() {
            document.getElementById('temp-value').textContent = this.value + '°C';
        });
        
        document.getElementById('volume-slider').addEventListener('input', function() {
            document.getElementById('volume-value').textContent = this.value + '%';
            fetch('/api/audio/volume', {
                method: 'PUT',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({volume: parseInt(this.value)})
            });
        });
    </script>
</body>
</html>
        """
    
    async def _get_settings_html(self) -> str:
        """Get settings HTML"""
        return """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Smart Shower OS - Settings</title>
    <style>
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 0;
            padding: 20px;
            background: #f5f5f5;
        }
        .container {
            max-width: 800px;
            margin: 0 auto;
            background: white;
            border-radius: 10px;
            padding: 20px;
            box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
        }
        .setting-group {
            margin: 20px 0;
            padding: 15px;
            border: 1px solid #ddd;
            border-radius: 5px;
        }
        .setting-item {
            margin: 10px 0;
        }
        label {
            display: block;
            margin-bottom: 5px;
            font-weight: bold;
        }
        input, select {
            width: 100%;
            padding: 8px;
            border: 1px solid #ddd;
            border-radius: 4px;
        }
        .button {
            background: #4CAF50;
            color: white;
            border: none;
            padding: 10px 20px;
            border-radius: 5px;
            cursor: pointer;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>Settings</h1>
        
        <div class="setting-group">
            <h3>Water Control</h3>
            <div class="setting-item">
                <label>Default Temperature (°C)</label>
                <input type="number" min="20" max="45" value="38" id="default-temp">
            </div>
            <div class="setting-item">
                <label>Maximum Temperature (°C)</label>
                <input type="number" min="30" max="50" value="45" id="max-temp">
            </div>
        </div>
        
        <div class="setting-group">
            <h3>Audio Settings</h3>
            <div class="setting-item">
                <label>Default Volume (%)</label>
                <input type="number" min="0" max="100" value="50" id="default-volume">
            </div>
            <div class="setting-item">
                <label>Audio Device</label>
                <select id="audio-device">
                    <option value="default">Default</option>
                    <option value="bluetooth">Bluetooth</option>
                </select>
            </div>
        </div>
        
        <div class="setting-group">
            <h3>Safety Settings</h3>
            <div class="setting-item">
                <label>Door Timeout (minutes)</label>
                <input type="number" min="1" max="30" value="10" id="door-timeout">
            </div>
            <div class="setting-item">
                <label>Maximum Shower Duration (minutes)</label>
                <input type="number" min="5" max="60" value="30" id="max-duration">
            </div>
        </div>
        
        <button class="button" onclick="saveSettings()">Save Settings</button>
    </div>
    
    <script>
        function saveSettings() {
            const settings = {
                default_temp: document.getElementById('default-temp').value,
                max_temp: document.getElementById('max-temp').value,
                default_volume: document.getElementById('default-volume').value,
                audio_device: document.getElementById('audio-device').value,
                door_timeout: document.getElementById('door-timeout').value,
                max_duration: document.getElementById('max-duration').value
            };
            
            // Save settings (would send to API in real implementation)
            console.log('Saving settings:', settings);
            alert('Settings saved!');
        }
    </script>
</body>
</html>
        """
    
    def set_system(self, system):
        """Set reference to main system"""
        self.system = system 