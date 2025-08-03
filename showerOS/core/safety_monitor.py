"""
Safety Monitor for Smart Shower
Handles door sensors, leak detection, and auto-shutoff features
"""

import asyncio
import logging
import time
from typing import Optional, Callable
from enum import Enum
from dataclasses import dataclass


class SafetyState(Enum):
    """Safety system states"""
    SAFE = "safe"
    WARNING = "warning"
    DANGER = "danger"
    EMERGENCY = "emergency"


class SensorState(Enum):
    """Sensor states"""
    OPEN = "open"
    CLOSED = "closed"
    UNKNOWN = "unknown"


@dataclass
class SafetyEvent:
    """Safety event information"""
    event_type: str
    timestamp: float
    severity: str
    message: str
    sensor_id: str = ""


class SafetyMonitor:
    """Monitors safety conditions and manages auto-shutoff"""
    
    def __init__(self, config):
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Safety state
        self.safety_state = SafetyState.SAFE
        self.door_state = SensorState.UNKNOWN
        self.leak_detected = False
        self.emergency_stop_active = False
        
        # Timing
        self.door_timer = None
        self.door_timer_duration = 600  # 10 minutes in seconds
        self.shower_start_time = None
        self.last_door_open_time = None
        
        # Sensors (simulated)
        self.door_sensor_active = False
        self.leak_sensor_active = False
        self.motion_sensor_active = False
        self.emergency_button_pressed = False
        
        # Event callbacks
        self.on_door_open: Optional[Callable] = None
        self.on_door_close: Optional[Callable] = None
        self.on_leak_detected: Optional[Callable] = None
        self.on_emergency_stop: Optional[Callable] = None
        self.on_safety_warning: Optional[Callable] = None
        
        # Control loop
        self.control_task = None
        self.is_running = False
        
        # Safety settings
        self.max_shower_duration = 1800  # 30 minutes
        self.door_timeout = 600  # 10 minutes
        self.leak_threshold = 0.1  # liters per minute
        self.temperature_limit = 45.0  # degrees Celsius
        
    async def initialize(self):
        """Initialize the safety monitoring system"""
        self.logger.info("Initializing safety monitoring system...")
        
        # Initialize sensors
        await self._initialize_sensors()
        
        # Load safety settings
        await self._load_safety_settings()
        
        # Initialize safety state
        await self._initialize_safety_state()
        
        self.logger.info("Safety monitoring system initialized")
    
    async def _initialize_sensors(self):
        """Initialize safety sensors"""
        # In a real system, this would initialize:
        # - Door sensors (magnetic, optical, or pressure)
        # - Leak sensors (moisture, flow, or pressure)
        # - Motion sensors (PIR, ultrasonic, or camera)
        # - Emergency stop button
        # - Temperature sensors
        
        self.logger.info("Safety sensors initialized (simulated)")
    
    async def _load_safety_settings(self):
        """Load safety settings from config"""
        settings = self.config.get('safety', {})
        self.door_timeout = settings.get('door_timeout', 600)  # 10 minutes
        self.max_shower_duration = settings.get('max_shower_duration', 1800)  # 30 minutes
        self.leak_threshold = settings.get('leak_threshold', 0.1)
        self.temperature_limit = settings.get('temperature_limit', 45.0)
        
        self.logger.info(f"Loaded safety settings - Door timeout: {self.door_timeout}s")
    
    async def _initialize_safety_state(self):
        """Initialize safety system state"""
        self.safety_state = SafetyState.SAFE
        self.door_state = SensorState.UNKNOWN
        self.leak_detected = False
        self.emergency_stop_active = False
        
        self.logger.info("Safety state initialized")
    
    async def start(self):
        """Start the safety monitoring system"""
        self.logger.info("Starting safety monitoring system...")
        self.is_running = True
        
        # Start control loop
        self.control_task = asyncio.create_task(self._control_loop())
        
        self.logger.info("Safety monitoring system started")
    
    async def shutdown(self):
        """Shutdown the safety monitoring system"""
        self.logger.info("Shutting down safety monitoring system...")
        self.is_running = False
        
        # Cancel door timer
        if self.door_timer:
            self.door_timer.cancel()
        
        # Cancel control task
        if self.control_task:
            self.control_task.cancel()
            try:
                await self.control_task
            except asyncio.CancelledError:
                pass
        
        self.logger.info("Safety monitoring system shutdown complete")
    
    async def start_shower_session(self):
        """Start a new shower session"""
        self.logger.info("Starting shower session...")
        
        self.shower_start_time = time.time()
        self.safety_state = SafetyState.SAFE
        
        # Start door monitoring
        await self.start_door_timer()
        
        self.logger.info("Shower session started")
    
    async def stop_shower_session(self):
        """Stop the current shower session"""
        self.logger.info("Stopping shower session...")
        
        # Cancel door timer
        if self.door_timer:
            self.door_timer.cancel()
            self.door_timer = None
        
        self.shower_start_time = None
        self.safety_state = SafetyState.SAFE
        
        self.logger.info("Shower session stopped")
    
    async def start_door_timer(self):
        """Start the door timeout timer"""
        if self.door_timer:
            self.door_timer.cancel()
        
        self.door_timer = asyncio.create_task(self._door_timeout_handler())
        self.logger.info(f"Door timer started ({self.door_timeout}s)")
    
    async def reset_door_timer(self):
        """Reset the door timeout timer"""
        if self.door_timer:
            self.door_timer.cancel()
        
        await self.start_door_timer()
        self.logger.info("Door timer reset")
    
    async def _door_timeout_handler(self):
        """Handle door timeout - auto-shutoff after 10 minutes"""
        try:
            await asyncio.sleep(self.door_timeout)
            
            # Check if door is still closed
            if self.door_state == SensorState.CLOSED:
                self.logger.warning(f"Door timeout reached ({self.door_timeout}s) - Auto-shutoff!")
                
                # Trigger emergency stop
                await self.emergency_stop("Door timeout - Auto-shutoff")
                
        except asyncio.CancelledError:
            # Timer was cancelled
            pass
    
    async def emergency_stop(self, reason: str = "Emergency stop"):
        """Trigger emergency stop"""
        self.logger.warning(f"EMERGENCY STOP: {reason}")
        
        self.emergency_stop_active = True
        self.safety_state = SafetyState.EMERGENCY
        
        # Trigger emergency stop event
        if self.on_emergency_stop:
            await self.on_emergency_stop()
    
    async def get_status(self):
        """Get current safety status"""
        door_time_remaining = None
        if self.door_timer and not self.door_timer.done():
            # Calculate remaining time (approximate)
            elapsed = time.time() - (self.shower_start_time or time.time())
            door_time_remaining = max(0, self.door_timeout - elapsed)
        
        return {
            'safety_state': self.safety_state.value,
            'door_state': self.door_state.value,
            'leak_detected': self.leak_detected,
            'emergency_stop_active': self.emergency_stop_active,
            'door_time_remaining': door_time_remaining,
            'shower_duration': time.time() - (self.shower_start_time or time.time()) if self.shower_start_time else 0
        }
    
    async def _control_loop(self):
        """Main control loop for safety monitoring"""
        while self.is_running:
            try:
                # Read sensors
                await self._read_sensors()
                
                # Check safety conditions
                await self._check_safety_conditions()
                
                # Update safety state
                await self._update_safety_state()
                
                await asyncio.sleep(0.1)  # 100ms control loop
                
            except Exception as e:
                self.logger.error(f"Error in safety control loop: {e}")
                await asyncio.sleep(1)
    
    async def _read_sensors(self):
        """Read safety sensors (simulated)"""
        # In a real system, this would read:
        # - Door sensors
        # - Leak sensors
        # - Motion sensors
        # - Emergency button
        # - Temperature sensors
        
        # Simulate door sensor
        old_door_state = self.door_state
        if self.door_sensor_active:
            self.door_state = SensorState.OPEN
        else:
            self.door_state = SensorState.CLOSED
        
        # Trigger door events
        if old_door_state != self.door_state:
            if self.door_state == SensorState.OPEN:
                self.last_door_open_time = time.time()
                if self.on_door_open:
                    await self.on_door_open()
            else:
                if self.on_door_close:
                    await self.on_door_close()
        
        # Simulate leak sensor
        if self.leak_sensor_active and not self.leak_detected:
            self.leak_detected = True
            if self.on_leak_detected:
                await self.on_leak_detected()
        
        # Simulate emergency button
        if self.emergency_button_pressed:
            await self.emergency_stop("Emergency button pressed")
    
    async def _check_safety_conditions(self):
        """Check for safety violations"""
        # Check shower duration
        if self.shower_start_time:
            duration = time.time() - self.shower_start_time
            if duration > self.max_shower_duration:
                self.logger.warning(f"Maximum shower duration exceeded ({duration}s)")
                await self.emergency_stop("Maximum shower duration exceeded")
        
        # Check for leaks
        if self.leak_detected:
            self.safety_state = SafetyState.DANGER
            if self.on_safety_warning:
                await self.on_safety_warning("Water leak detected")
        
        # Check door state
        if self.door_state == SensorState.CLOSED and self.shower_start_time:
            # Door is closed during shower - this is normal
            pass
        elif self.door_state == SensorState.OPEN and self.shower_start_time:
            # Door opened during shower - reset timer
            await self.reset_door_timer()
    
    async def _update_safety_state(self):
        """Update overall safety state"""
        old_state = self.safety_state
        
        if self.emergency_stop_active:
            self.safety_state = SafetyState.EMERGENCY
        elif self.leak_detected:
            self.safety_state = SafetyState.DANGER
        elif self.door_state == SensorState.CLOSED and self.shower_start_time:
            # Door closed during shower - check timer
            if self.door_timer and self.door_timer.done():
                self.safety_state = SafetyState.WARNING
            else:
                self.safety_state = SafetyState.SAFE
        else:
            self.safety_state = SafetyState.SAFE
        
        if old_state != self.safety_state:
            self.logger.info(f"Safety state changed: {old_state.value} -> {self.safety_state.value}")
    
    async def test_sensors(self):
        """Test all safety sensors"""
        self.logger.info("Testing safety sensors...")
        
        # Test door sensor
        self.door_sensor_active = True
        await asyncio.sleep(0.1)
        self.door_sensor_active = False
        await asyncio.sleep(0.1)
        
        # Test leak sensor
        self.leak_sensor_active = True
        await asyncio.sleep(0.1)
        self.leak_sensor_active = False
        
        # Test motion sensor
        self.motion_sensor_active = True
        await asyncio.sleep(0.1)
        self.motion_sensor_active = False
        
        self.logger.info("Sensor test complete")
    
    async def calibrate_sensors(self):
        """Calibrate safety sensors"""
        self.logger.info("Calibrating safety sensors...")
        
        # In a real system, this would:
        # - Calibrate door sensors
        # - Calibrate leak sensors
        # - Calibrate motion sensors
        # - Test emergency button
        
        self.logger.info("Sensor calibration complete")
    
    async def get_safety_log(self):
        """Get safety event log"""
        # In a real system, this would return actual safety events
        return [
            {
                'timestamp': time.time(),
                'event': 'System initialized',
                'severity': 'info'
            }
        ]
    
    # Simulation methods for testing
    async def simulate_door_open(self):
        """Simulate door opening"""
        self.door_sensor_active = True
        self.logger.info("Simulating door open")
    
    async def simulate_door_close(self):
        """Simulate door closing"""
        self.door_sensor_active = False
        self.logger.info("Simulating door close")
    
    async def simulate_leak(self):
        """Simulate water leak"""
        self.leak_sensor_active = True
        self.logger.info("Simulating water leak")
    
    async def simulate_emergency_button(self):
        """Simulate emergency button press"""
        self.emergency_button_pressed = True
        self.logger.info("Simulating emergency button press")
        await asyncio.sleep(0.1)
        self.emergency_button_pressed = False 