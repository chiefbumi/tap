"""
Water Control System for Smart Shower
Manages water flow, temperature, and valve operations
"""

import asyncio
import logging
import time
from typing import Optional, Callable
from dataclasses import dataclass
from enum import Enum


class ValveState(Enum):
    """Valve states"""
    CLOSED = "closed"
    OPEN = "open"
    PARTIAL = "partial"


class FlowState(Enum):
    """Water flow states"""
    STOPPED = "stopped"
    FLOWING = "flowing"
    ADJUSTING = "adjusting"


@dataclass
class WaterSettings:
    """Water control settings"""
    target_temperature: float = 38.0
    max_temperature: float = 45.0
    min_temperature: float = 20.0
    flow_rate: float = 8.0  # liters per minute
    pressure: float = 2.0    # bar


class WaterController:
    """Controls water flow, temperature, and valve operations"""
    
    def __init__(self, config):
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Water control state
        self.current_temperature = 20.0
        self.target_temperature = 38.0
        self.flow_rate = 0.0
        self.pressure = 0.0
        self.valve_state = ValveState.CLOSED
        self.flow_state = FlowState.STOPPED
        
        # Hardware simulation (replace with actual hardware)
        self.hot_valve_open = False
        self.cold_valve_open = False
        self.mixer_valve_position = 0.5  # 0.0 = cold, 1.0 = hot
        
        # Event callbacks
        self.on_flow_start: Optional[Callable] = None
        self.on_flow_stop: Optional[Callable] = None
        self.on_temperature_change: Optional[Callable] = None
        self.on_pressure_change: Optional[Callable] = None
        
        # Control loop
        self.control_task = None
        self.is_running = False
        
    async def initialize(self):
        """Initialize the water control system"""
        self.logger.info("Initializing water control system...")
        
        # Initialize hardware (simulated)
        await self._initialize_hardware()
        
        # Load settings
        await self._load_settings()
        
        self.logger.info("Water control system initialized")
    
    async def _initialize_hardware(self):
        """Initialize hardware components"""
        # In a real system, this would initialize:
        # - Solenoid valves
        # - Temperature sensors
        # - Flow sensors
        # - Pressure sensors
        # - Mixing valve motors
        
        self.logger.info("Hardware initialized (simulated)")
    
    async def _load_settings(self):
        """Load water control settings from config"""
        settings = self.config.get('water_control', {})
        self.target_temperature = settings.get('default_temperature', 38.0)
        self.max_temperature = settings.get('max_temperature', 45.0)
        self.min_temperature = settings.get('min_temperature', 20.0)
        
        self.logger.info(f"Loaded settings - Target temp: {self.target_temperature}°C")
    
    async def start(self):
        """Start the water control system"""
        self.logger.info("Starting water control system...")
        self.is_running = True
        
        # Start control loop
        self.control_task = asyncio.create_task(self._control_loop())
        
        self.logger.info("Water control system started")
    
    async def shutdown(self):
        """Shutdown the water control system"""
        self.logger.info("Shutting down water control system...")
        self.is_running = False
        
        # Stop water flow
        await self.stop_flow()
        
        # Cancel control task
        if self.control_task:
            self.control_task.cancel()
            try:
                await self.control_task
            except asyncio.CancelledError:
                pass
        
        self.logger.info("Water control system shutdown complete")
    
    async def start_flow(self, temperature: float = None):
        """Start water flow at specified temperature"""
        if temperature is not None:
            self.target_temperature = max(self.min_temperature, min(self.max_temperature, temperature))
        
        self.logger.info(f"Starting water flow at {self.target_temperature}°C")
        
        # Open valves
        await self._open_valves()
        
        # Start flow
        self.flow_state = FlowState.ADJUSTING
        self.flow_rate = 8.0  # liters per minute
        
        # Trigger event
        if self.on_flow_start:
            await self.on_flow_start(self.target_temperature)
        
        self.logger.info("Water flow started")
    
    async def stop_flow(self):
        """Stop water flow"""
        self.logger.info("Stopping water flow...")
        
        # Close valves
        await self._close_valves()
        
        # Stop flow
        self.flow_state = FlowState.STOPPED
        self.flow_rate = 0.0
        
        # Trigger event
        if self.on_flow_stop:
            await self.on_flow_stop()
        
        self.logger.info("Water flow stopped")
    
    async def set_temperature(self, temperature: float):
        """Set target water temperature"""
        temperature = max(self.min_temperature, min(self.max_temperature, temperature))
        
        if abs(temperature - self.target_temperature) > 0.5:
            self.logger.info(f"Setting temperature to {temperature}°C")
            self.target_temperature = temperature
            await self._adjust_mixer_valve()
    
    async def set_flow_rate(self, flow_rate: float):
        """Set water flow rate"""
        flow_rate = max(0.0, min(15.0, flow_rate))  # 0-15 L/min
        
        self.logger.info(f"Setting flow rate to {flow_rate} L/min")
        self.flow_rate = flow_rate
        await self._adjust_flow_valves()
    
    async def get_status(self):
        """Get current water control status"""
        return {
            'temperature': {
                'current': self.current_temperature,
                'target': self.target_temperature,
                'min': self.min_temperature,
                'max': self.max_temperature
            },
            'flow': {
                'state': self.flow_state.value,
                'rate': self.flow_rate,
                'pressure': self.pressure
            },
            'valves': {
                'hot': self.hot_valve_open,
                'cold': self.cold_valve_open,
                'mixer_position': self.mixer_valve_position
            }
        }
    
    async def _control_loop(self):
        """Main control loop for water management"""
        while self.is_running:
            try:
                # Read sensors (simulated)
                await self._read_sensors()
                
                # Adjust temperature if needed
                if self.flow_state == FlowState.FLOWING:
                    await self._adjust_temperature()
                
                # Monitor for issues
                await self._check_safety()
                
                await asyncio.sleep(0.1)  # 100ms control loop
                
            except Exception as e:
                self.logger.error(f"Error in water control loop: {e}")
                await asyncio.sleep(1)
    
    async def _read_sensors(self):
        """Read water sensors (simulated)"""
        # In a real system, this would read:
        # - Temperature sensors
        # - Flow sensors
        # - Pressure sensors
        
        # Simulate temperature adjustment
        if self.flow_state != FlowState.STOPPED:
            temp_diff = self.target_temperature - self.current_temperature
            if abs(temp_diff) > 0.1:
                self.current_temperature += temp_diff * 0.1  # Gradual adjustment
                
                # Trigger temperature change event
                if self.on_temperature_change:
                    await self.on_temperature_change(self.current_temperature)
    
    async def _adjust_temperature(self):
        """Adjust water temperature by controlling mixer valve"""
        temp_diff = self.target_temperature - self.current_temperature
        
        if abs(temp_diff) > 0.5:
            # Adjust mixer valve position
            if temp_diff > 0:
                # Need hotter water
                self.mixer_valve_position = min(1.0, self.mixer_valve_position + 0.01)
            else:
                # Need colder water
                self.mixer_valve_position = max(0.0, self.mixer_valve_position - 0.01)
            
            await self._adjust_mixer_valve()
    
    async def _adjust_mixer_valve(self):
        """Adjust the mixing valve position"""
        # In a real system, this would control a motorized mixing valve
        self.logger.debug(f"Adjusting mixer valve to position {self.mixer_valve_position}")
    
    async def _adjust_flow_valves(self):
        """Adjust flow control valves"""
        # In a real system, this would control flow control valves
        self.logger.debug(f"Adjusting flow valves for rate {self.flow_rate} L/min")
    
    async def _open_valves(self):
        """Open water control valves"""
        self.logger.debug("Opening water valves...")
        
        # Open hot and cold supply valves
        self.hot_valve_open = True
        self.cold_valve_open = True
        
        # Set initial mixer position
        self.mixer_valve_position = 0.5
        
        self.valve_state = ValveState.OPEN
    
    async def _close_valves(self):
        """Close water control valves"""
        self.logger.debug("Closing water valves...")
        
        # Close all valves
        self.hot_valve_open = False
        self.cold_valve_open = False
        self.mixer_valve_position = 0.0
        
        self.valve_state = ValveState.CLOSED
    
    async def _check_safety(self):
        """Check for safety issues"""
        # Check temperature limits
        if self.current_temperature > self.max_temperature:
            self.logger.warning(f"Temperature too high: {self.current_temperature}°C")
            await self.stop_flow()
        
        # Check pressure limits
        if self.pressure > 5.0:  # 5 bar max
            self.logger.warning(f"Pressure too high: {self.pressure} bar")
            await self.stop_flow()
        
        # Check for flow anomalies
        if self.flow_state == FlowState.FLOWING and self.flow_rate < 0.5:
            self.logger.warning("Low flow rate detected")
    
    async def emergency_stop(self):
        """Emergency stop - immediately close all valves"""
        self.logger.warning("EMERGENCY STOP - Closing all valves!")
        
        # Immediately close all valves
        self.hot_valve_open = False
        self.cold_valve_open = False
        self.mixer_valve_position = 0.0
        self.valve_state = ValveState.CLOSED
        self.flow_state = FlowState.STOPPED
        self.flow_rate = 0.0
        
        # Trigger stop event
        if self.on_flow_stop:
            await self.on_flow_stop()
    
    async def calibrate_sensors(self):
        """Calibrate water sensors"""
        self.logger.info("Calibrating water sensors...")
        
        # In a real system, this would:
        # - Calibrate temperature sensors
        # - Calibrate flow sensors
        # - Calibrate pressure sensors
        
        self.logger.info("Sensor calibration complete")
    
    async def get_usage_stats(self):
        """Get water usage statistics"""
        # In a real system, this would return actual usage data
        return {
            'total_flow': 0.0,  # liters
            'session_count': 0,
            'average_temperature': 38.0,
            'average_duration': 0.0  # minutes
        } 