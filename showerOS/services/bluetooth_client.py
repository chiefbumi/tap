"""
Bluetooth Client for Smart Shower OS
Handles Bluetooth device discovery and audio streaming
"""

import asyncio
import logging
import subprocess
import time
from typing import Dict, Any, List, Optional
from dataclasses import dataclass


@dataclass
class BluetoothDevice:
    """Bluetooth device information"""
    address: str
    name: str
    device_type: str
    connected: bool = False
    paired: bool = False


class BluetoothClient:
    """Bluetooth client for audio streaming"""
    
    def __init__(self, config):
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Bluetooth settings
        self.device_name = config.get_credential('bluetooth.device_name', 'Smart Shower')
        self.pin_code = config.get_credential('bluetooth.pin_code', '0000')
        
        # Bluetooth state
        self.is_enabled = False
        self.is_discovering = False
        self.connected_device = None
        
        # Device lists
        self.discovered_devices: List[BluetoothDevice] = []
        self.paired_devices: List[BluetoothDevice] = []
        
        # Audio streaming
        self.audio_stream_active = False
        self.audio_process = None
        
    async def initialize(self):
        """Initialize the Bluetooth client"""
        self.logger.info("Initializing Bluetooth client...")
        
        # Check if Bluetooth is available
        await self._check_bluetooth_availability()
        
        # Load paired devices
        await self._load_paired_devices()
        
        self.logger.info("Bluetooth client initialized")
    
    async def _check_bluetooth_availability(self):
        """Check if Bluetooth is available and enabled"""
        try:
            # Check if bluetoothctl is available
            result = subprocess.run(['bluetoothctl', '--version'], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                self.logger.info("bluetoothctl is available")
                
                # Check if Bluetooth is enabled
                result = subprocess.run(['bluetoothctl', 'show'], 
                                      capture_output=True, text=True)
                if 'Powered: yes' in result.stdout:
                    self.is_enabled = True
                    self.logger.info("Bluetooth is enabled")
                else:
                    self.logger.warning("Bluetooth is disabled")
            else:
                self.logger.warning("bluetoothctl not found")
                
        except FileNotFoundError:
            self.logger.warning("bluetoothctl not available")
        except Exception as e:
            self.logger.error(f"Error checking Bluetooth availability: {e}")
    
    async def _load_paired_devices(self):
        """Load list of paired devices"""
        try:
            result = subprocess.run(['bluetoothctl', 'paired-devices'], 
                                  capture_output=True, text=True)
            
            if result.returncode == 0:
                lines = result.stdout.strip().split('\n')
                for line in lines:
                    if line.strip():
                        # Parse device info (format: Device XX:XX:XX:XX:XX:XX DeviceName)
                        parts = line.split()
                        if len(parts) >= 2:
                            address = parts[1]
                            name = ' '.join(parts[2:]) if len(parts) > 2 else 'Unknown'
                            
                            device = BluetoothDevice(
                                address=address,
                                name=name,
                                device_type='unknown',
                                paired=True
                            )
                            self.paired_devices.append(device)
                
                self.logger.info(f"Loaded {len(self.paired_devices)} paired devices")
            
        except Exception as e:
            self.logger.error(f"Error loading paired devices: {e}")
    
    async def shutdown(self):
        """Shutdown the Bluetooth client"""
        self.logger.info("Shutting down Bluetooth client...")
        
        # Disconnect from current device
        if self.connected_device:
            await self.disconnect()
        
        # Stop audio streaming
        if self.audio_stream_active:
            await self.stop_audio()
        
        self.logger.info("Bluetooth client shutdown complete")
    
    async def enable_bluetooth(self) -> bool:
        """Enable Bluetooth"""
        try:
            result = subprocess.run(['bluetoothctl', 'power', 'on'], 
                                  capture_output=True, text=True)
            
            if result.returncode == 0:
                self.is_enabled = True
                self.logger.info("Bluetooth enabled")
                return True
            else:
                self.logger.error("Failed to enable Bluetooth")
                return False
                
        except Exception as e:
            self.logger.error(f"Error enabling Bluetooth: {e}")
            return False
    
    async def disable_bluetooth(self) -> bool:
        """Disable Bluetooth"""
        try:
            result = subprocess.run(['bluetoothctl', 'power', 'off'], 
                                  capture_output=True, text=True)
            
            if result.returncode == 0:
                self.is_enabled = False
                self.logger.info("Bluetooth disabled")
                return True
            else:
                self.logger.error("Failed to disable Bluetooth")
                return False
                
        except Exception as e:
            self.logger.error(f"Error disabling Bluetooth: {e}")
            return False
    
    async def start_discovery(self) -> bool:
        """Start Bluetooth device discovery"""
        try:
            if not self.is_enabled:
                await self.enable_bluetooth()
            
            result = subprocess.run(['bluetoothctl', 'scan', 'on'], 
                                  capture_output=True, text=True)
            
            if result.returncode == 0:
                self.is_discovering = True
                self.logger.info("Started Bluetooth discovery")
                return True
            else:
                self.logger.error("Failed to start Bluetooth discovery")
                return False
                
        except Exception as e:
            self.logger.error(f"Error starting discovery: {e}")
            return False
    
    async def stop_discovery(self) -> bool:
        """Stop Bluetooth device discovery"""
        try:
            result = subprocess.run(['bluetoothctl', 'scan', 'off'], 
                                  capture_output=True, text=True)
            
            if result.returncode == 0:
                self.is_discovering = False
                self.logger.info("Stopped Bluetooth discovery")
                return True
            else:
                self.logger.error("Failed to stop Bluetooth discovery")
                return False
                
        except Exception as e:
            self.logger.error(f"Error stopping discovery: {e}")
            return False
    
    async def get_devices(self) -> List[Dict[str, Any]]:
        """Get list of discovered and paired devices"""
        devices = []
        
        # Add paired devices
        for device in self.paired_devices:
            devices.append({
                'address': device.address,
                'name': device.name,
                'type': device.device_type,
                'paired': device.paired,
                'connected': device.connected
            })
        
        # Add discovered devices
        for device in self.discovered_devices:
            devices.append({
                'address': device.address,
                'name': device.name,
                'type': device.device_type,
                'paired': device.paired,
                'connected': device.connected
            })
        
        return devices
    
    async def connect(self, device_id: str) -> bool:
        """Connect to a Bluetooth device"""
        try:
            # Find device by address or name
            device = None
            for d in self.paired_devices + self.discovered_devices:
                if d.address == device_id or d.name == device_id:
                    device = d
                    break
            
            if not device:
                self.logger.error(f"Device not found: {device_id}")
                return False
            
            # Connect to device
            result = subprocess.run(['bluetoothctl', 'connect', device.address], 
                                  capture_output=True, text=True)
            
            if result.returncode == 0 or 'Connected: yes' in result.stdout:
                device.connected = True
                self.connected_device = device
                self.logger.info(f"Connected to {device.name}")
                return True
            else:
                self.logger.error(f"Failed to connect to {device.name}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error connecting to device: {e}")
            return False
    
    async def disconnect(self) -> bool:
        """Disconnect from current device"""
        try:
            if not self.connected_device:
                return True
            
            result = subprocess.run(['bluetoothctl', 'disconnect', self.connected_device.address], 
                                  capture_output=True, text=True)
            
            if result.returncode == 0:
                self.connected_device.connected = False
                self.connected_device = None
                self.logger.info("Disconnected from Bluetooth device")
                return True
            else:
                self.logger.error("Failed to disconnect from device")
                return False
                
        except Exception as e:
            self.logger.error(f"Error disconnecting from device: {e}")
            return False
    
    async def pair_device(self, device_id: str) -> bool:
        """Pair with a Bluetooth device"""
        try:
            # Find device
            device = None
            for d in self.discovered_devices:
                if d.address == device_id or d.name == device_id:
                    device = d
                    break
            
            if not device:
                self.logger.error(f"Device not found: {device_id}")
                return False
            
            # Pair with device
            result = subprocess.run(['bluetoothctl', 'pair', device.address], 
                                  capture_output=True, text=True)
            
            if result.returncode == 0:
                device.paired = True
                self.paired_devices.append(device)
                self.logger.info(f"Paired with {device.name}")
                return True
            else:
                self.logger.error(f"Failed to pair with {device.name}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error pairing with device: {e}")
            return False
    
    async def start_audio(self) -> bool:
        """Start Bluetooth audio streaming"""
        try:
            if not self.connected_device:
                self.logger.error("No device connected")
                return False
            
            # Start audio streaming (this would depend on the specific audio system)
            # For now, we'll simulate it
            self.audio_stream_active = True
            self.logger.info(f"Started audio streaming to {self.connected_device.name}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error starting audio streaming: {e}")
            return False
    
    async def stop_audio(self) -> bool:
        """Stop Bluetooth audio streaming"""
        try:
            if self.audio_process:
                self.audio_process.terminate()
                try:
                    await asyncio.wait_for(self.audio_process.wait(), timeout=5.0)
                except asyncio.TimeoutError:
                    self.audio_process.kill()
                self.audio_process = None
            
            self.audio_stream_active = False
            self.logger.info("Stopped audio streaming")
            return True
            
        except Exception as e:
            self.logger.error(f"Error stopping audio streaming: {e}")
            return False
    
    async def set_volume(self, volume: int) -> bool:
        """Set Bluetooth audio volume"""
        try:
            volume = max(0, min(100, volume))
            
            # This would set the volume on the connected device
            # Implementation depends on the specific Bluetooth audio system
            
            self.logger.info(f"Set Bluetooth volume to {volume}%")
            return True
            
        except Exception as e:
            self.logger.error(f"Error setting volume: {e}")
            return False
    
    async def get_device_info(self, device_id: str) -> Optional[Dict[str, Any]]:
        """Get detailed information about a device"""
        try:
            result = subprocess.run(['bluetoothctl', 'info', device_id], 
                                  capture_output=True, text=True)
            
            if result.returncode == 0:
                info = {}
                lines = result.stdout.strip().split('\n')
                
                for line in lines:
                    if ':' in line:
                        key, value = line.split(':', 1)
                        info[key.strip()] = value.strip()
                
                return info
            else:
                return None
                
        except Exception as e:
            self.logger.error(f"Error getting device info: {e}")
            return None
    
    async def trust_device(self, device_id: str) -> bool:
        """Trust a Bluetooth device"""
        try:
            result = subprocess.run(['bluetoothctl', 'trust', device_id], 
                                  capture_output=True, text=True)
            
            if result.returncode == 0:
                self.logger.info(f"Trusted device: {device_id}")
                return True
            else:
                self.logger.error(f"Failed to trust device: {device_id}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error trusting device: {e}")
            return False
    
    async def remove_device(self, device_id: str) -> bool:
        """Remove a paired device"""
        try:
            result = subprocess.run(['bluetoothctl', 'remove', device_id], 
                                  capture_output=True, text=True)
            
            if result.returncode == 0:
                # Remove from our lists
                self.paired_devices = [d for d in self.paired_devices if d.address != device_id]
                self.discovered_devices = [d for d in self.discovered_devices if d.address != device_id]
                
                self.logger.info(f"Removed device: {device_id}")
                return True
            else:
                self.logger.error(f"Failed to remove device: {device_id}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error removing device: {e}")
            return False
    
    def is_available(self) -> bool:
        """Check if Bluetooth is available"""
        return self.is_enabled
    
    async def get_status(self) -> Dict[str, Any]:
        """Get Bluetooth client status"""
        return {
            'enabled': self.is_enabled,
            'discovering': self.is_discovering,
            'connected_device': {
                'address': self.connected_device.address,
                'name': self.connected_device.name
            } if self.connected_device else None,
            'audio_stream_active': self.audio_stream_active,
            'paired_devices_count': len(self.paired_devices),
            'discovered_devices_count': len(self.discovered_devices)
        }
    
    async def scan_for_devices(self, duration: int = 10) -> List[Dict[str, Any]]:
        """Scan for Bluetooth devices"""
        try:
            # Start discovery
            await self.start_discovery()
            
            # Wait for discovery
            await asyncio.sleep(duration)
            
            # Stop discovery
            await self.stop_discovery()
            
            # Get discovered devices
            return await self.get_devices()
            
        except Exception as e:
            self.logger.error(f"Error scanning for devices: {e}")
            return []
    
    async def _parse_discovery_output(self, output: str):
        """Parse discovery output to find devices"""
        lines = output.strip().split('\n')
        devices = []
        
        for line in lines:
            if 'Device' in line and 'XX:XX:XX:XX:XX:XX' in line:
                # Parse device line
                parts = line.split()
                if len(parts) >= 2:
                    address = parts[1]
                    name = ' '.join(parts[2:]) if len(parts) > 2 else 'Unknown'
                    
                    device = BluetoothDevice(
                        address=address,
                        name=name,
                        device_type='unknown'
                    )
                    devices.append(device)
        
        return devices 