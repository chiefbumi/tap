#!/usr/bin/env python3
"""
Smart Shower OS - Main Entry Point
Controls water flow, audio streaming, and safety monitoring
"""

import asyncio
import logging
import signal
import sys
import time
from pathlib import Path
from typing import Dict, Any

# Add the project root to Python path
sys.path.append(str(Path(__file__).parent))

from core.water_control import WaterController
from core.audio_manager import AudioManager
from core.safety_monitor import SafetyMonitor
from core.mobile_api import MobileAPI
from web.server import WebServer
from utils.config_manager import ConfigManager
from utils.logger import setup_logging


class SmartShowerOS:
    """Main controller for the Smart Shower Operating System"""
    
    def __init__(self):
        self.config = ConfigManager()
        self.logger = logging.getLogger(__name__)
        
        # Core components
        self.water_controller = None
        self.audio_manager = None
        self.safety_monitor = None
        self.mobile_api = None
        self.web_server = None
        
        # System state
        self.is_running = False
        self.shower_active = False
        self.emergency_stop = False
        
    async def initialize(self):
        """Initialize all system components"""
        try:
            self.logger.info("Initializing Smart Shower OS...")
            
            # Initialize core components
            self.water_controller = WaterController(self.config)
            self.audio_manager = AudioManager(self.config)
            self.safety_monitor = SafetyMonitor(self.config)
            self.mobile_api = MobileAPI(self.config)
            self.web_server = WebServer(self.config)
            
            # Initialize components
            await self.water_controller.initialize()
            await self.audio_manager.initialize()
            await self.safety_monitor.initialize()
            await self.mobile_api.initialize()
            await self.web_server.initialize()
            
            # Set up event handlers
            self._setup_event_handlers()
            
            self.logger.info("Smart Shower OS initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize system: {e}")
            raise
    
    def _setup_event_handlers(self):
        """Set up event handlers for system components"""
        # Water controller events
        self.water_controller.on_flow_start = self._on_water_flow_start
        self.water_controller.on_flow_stop = self._on_water_flow_stop
        self.water_controller.on_temperature_change = self._on_temperature_change
        
        # Safety monitor events
        self.safety_monitor.on_door_open = self._on_door_open
        self.safety_monitor.on_door_close = self._on_door_close
        self.safety_monitor.on_leak_detected = self._on_leak_detected
        self.safety_monitor.on_emergency_stop = self._on_emergency_stop
        
        # Audio manager events
        self.audio_manager.on_playback_start = self._on_audio_start
        self.audio_manager.on_playback_stop = self._on_audio_stop
        
        # Mobile API events
        self.mobile_api.on_shower_start_request = self._on_shower_start_request
        self.mobile_api.on_shower_stop_request = self._on_shower_stop_request
        self.mobile_api.on_audio_control_request = self._on_audio_control_request
    
    async def start(self):
        """Start the smart shower system"""
        try:
            self.logger.info("Starting Smart Shower OS...")
            self.is_running = True
            
            # Start all components
            await self.water_controller.start()
            await self.audio_manager.start()
            await self.safety_monitor.start()
            await self.mobile_api.start()
            await self.web_server.start()
            
            self.logger.info("Smart Shower OS started successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to start system: {e}")
            await self.shutdown()
            raise
    
    async def shutdown(self):
        """Shutdown the system safely"""
        self.logger.info("Shutting down Smart Shower OS...")
        self.is_running = False
        
        # Stop shower if active
        if self.shower_active:
            await self.stop_shower()
        
        # Shutdown components
        if self.water_controller:
            await self.water_controller.shutdown()
        if self.audio_manager:
            await self.audio_manager.shutdown()
        if self.safety_monitor:
            await self.safety_monitor.shutdown()
        if self.mobile_api:
            await self.mobile_api.shutdown()
        if self.web_server:
            await self.web_server.shutdown()
        
        self.logger.info("Smart Shower OS shutdown complete")
    
    async def start_shower(self, temperature: float = 38.0, audio_source: str = None):
        """Start the shower with specified settings"""
        try:
            self.logger.info(f"Starting shower - Temperature: {temperature}°C, Audio: {audio_source}")
            
            # Start water flow
            await self.water_controller.start_flow(temperature)
            
            # Start audio if specified
            if audio_source:
                await self.audio_manager.start_playback(audio_source)
            
            # Start safety monitoring
            await self.safety_monitor.start_shower_session()
            
            self.shower_active = True
            self.logger.info("Shower started successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to start shower: {e}")
            raise
    
    async def stop_shower(self):
        """Stop the shower"""
        try:
            self.logger.info("Stopping shower...")
            
            # Stop water flow
            await self.water_controller.stop_flow()
            
            # Stop audio
            await self.audio_manager.stop_playback()
            
            # Stop safety monitoring
            await self.safety_monitor.stop_shower_session()
            
            self.shower_active = False
            self.logger.info("Shower stopped successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to stop shower: {e}")
            raise
    
    # Event handlers
    async def _on_water_flow_start(self, temperature: float):
        """Handle water flow start event"""
        self.logger.info(f"Water flow started at {temperature}°C")
    
    async def _on_water_flow_stop(self):
        """Handle water flow stop event"""
        self.logger.info("Water flow stopped")
    
    async def _on_temperature_change(self, temperature: float):
        """Handle temperature change event"""
        self.logger.info(f"Water temperature changed to {temperature}°C")
    
    async def _on_door_open(self):
        """Handle door open event"""
        self.logger.info("Shower door opened")
        # Reset safety timer
        await self.safety_monitor.reset_door_timer()
    
    async def _on_door_close(self):
        """Handle door close event"""
        self.logger.info("Shower door closed")
        # Start safety timer
        await self.safety_monitor.start_door_timer()
    
    async def _on_leak_detected(self):
        """Handle water leak detection"""
        self.logger.warning("Water leak detected!")
        await self.stop_shower()
        # Send emergency notification
        await self.mobile_api.send_emergency_notification("Water leak detected!")
    
    async def _on_emergency_stop(self):
        """Handle emergency stop"""
        self.logger.warning("Emergency stop activated!")
        self.emergency_stop = True
        await self.stop_shower()
        await self.mobile_api.send_emergency_notification("Emergency stop activated!")
    
    async def _on_audio_start(self, source: str):
        """Handle audio playback start"""
        self.logger.info(f"Audio playback started from {source}")
    
    async def _on_audio_stop(self):
        """Handle audio playback stop"""
        self.logger.info("Audio playback stopped")
    
    async def _on_shower_start_request(self, data: Dict[str, Any]):
        """Handle shower start request from mobile app"""
        temperature = data.get('temperature', 38.0)
        audio_source = data.get('audio_source')
        await self.start_shower(temperature, audio_source)
    
    async def _on_shower_stop_request(self):
        """Handle shower stop request from mobile app"""
        await self.stop_shower()
    
    async def _on_audio_control_request(self, data: Dict[str, Any]):
        """Handle audio control request from mobile app"""
        action = data.get('action')
        if action == 'play':
            await self.audio_manager.start_playback(data.get('source'))
        elif action == 'pause':
            await self.audio_manager.pause_playback()
        elif action == 'resume':
            await self.audio_manager.resume_playback()
        elif action == 'stop':
            await self.audio_manager.stop_playback()
        elif action == 'volume':
            await self.audio_manager.set_volume(data.get('volume', 50))
    
    async def run(self):
        """Main system loop"""
        try:
            await self.initialize()
            await self.start()
            
            # Main event loop
            while self.is_running:
                await asyncio.sleep(1)
                
                # Check for emergency stop
                if self.emergency_stop:
                    self.logger.warning("Emergency stop active - system paused")
                    await asyncio.sleep(5)
                    self.emergency_stop = False
                
        except KeyboardInterrupt:
            self.logger.info("Received shutdown signal")
        except Exception as e:
            self.logger.error(f"System error: {e}")
        finally:
            await self.shutdown()


def signal_handler(signum, frame):
    """Handle system signals for graceful shutdown"""
    print("\nReceived shutdown signal. Shutting down gracefully...")
    sys.exit(0)


async def main():
    """Main entry point"""
    # Set up signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Set up logging
    setup_logging()
    logger = logging.getLogger(__name__)
    
    # Create and run the system
    shower_os = SmartShowerOS()
    
    try:
        await shower_os.run()
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main()) 