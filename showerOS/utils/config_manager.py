"""
Configuration Manager for Smart Shower OS
Handles loading and managing system settings
"""

import os
import yaml
import logging
from pathlib import Path
from typing import Dict, Any, Optional


class ConfigManager:
    """Manages system configuration"""
    
    def __init__(self, config_path: str = None):
        self.logger = logging.getLogger(__name__)
        
        # Configuration paths
        if config_path is None:
            self.config_dir = Path(__file__).parent.parent / 'config'
        else:
            self.config_dir = Path(config_path)
        
        self.settings_file = self.config_dir / 'settings.yaml'
        self.credentials_file = self.config_dir / 'credentials.yaml'
        
        # Configuration data
        self.settings: Dict[str, Any] = {}
        self.credentials: Dict[str, Any] = {}
        
        # Load configuration
        self._load_configuration()
    
    def _load_configuration(self):
        """Load configuration from files"""
        try:
            # Create config directory if it doesn't exist
            self.config_dir.mkdir(parents=True, exist_ok=True)
            
            # Load settings
            if self.settings_file.exists():
                with open(self.settings_file, 'r') as f:
                    self.settings = yaml.safe_load(f) or {}
                self.logger.info(f"Loaded settings from {self.settings_file}")
            else:
                self._create_default_settings()
            
            # Load credentials
            if self.credentials_file.exists():
                with open(self.credentials_file, 'r') as f:
                    self.credentials = yaml.safe_load(f) or {}
                self.logger.info(f"Loaded credentials from {self.credentials_file}")
            else:
                self._create_default_credentials()
                
        except Exception as e:
            self.logger.error(f"Error loading configuration: {e}")
            self._create_default_configuration()
    
    def _create_default_settings(self):
        """Create default settings file"""
        default_settings = {
            'system': {
                'name': 'Smart Shower OS',
                'version': '1.0.0',
                'debug': False,
                'log_level': 'INFO'
            },
            'water_control': {
                'default_temperature': 38.0,
                'max_temperature': 45.0,
                'min_temperature': 20.0,
                'default_flow_rate': 8.0,
                'max_flow_rate': 15.0,
                'pressure_limit': 5.0
            },
            'audio': {
                'default_volume': 50,
                'audio_device': 'default',
                'audio_format': 'mp3',
                'sample_rate': 44100,
                'local_music_path': './music',
                'bluetooth_enabled': True
            },
            'safety': {
                'door_timeout': 600,  # 10 minutes
                'max_shower_duration': 1800,  # 30 minutes
                'leak_threshold': 0.1,
                'temperature_limit': 45.0,
                'emergency_stop_enabled': True
            },
            'mobile_api': {
                'host': '0.0.0.0',
                'port': 8080,
                'websocket_port': 8081,
                'session_timeout': 3600,
                'cors_enabled': True
            },
            'web': {
                'host': '0.0.0.0',
                'port': 8082,
                'static_path': './web/static',
                'template_path': './web/templates'
            },
            'logging': {
                'level': 'INFO',
                'file': './logs/shower.log',
                'max_size': 10485760,  # 10MB
                'backup_count': 5
            },
            'hardware': {
                'simulation_mode': True,
                'gpio_enabled': False,
                'i2c_enabled': False,
                'spi_enabled': False
            }
        }
        
        self.settings = default_settings
        self._save_settings()
        self.logger.info("Created default settings file")
    
    def _create_default_credentials(self):
        """Create default credentials file"""
        default_credentials = {
            'spotify': {
                'client_id': '',
                'client_secret': '',
                'redirect_uri': 'http://localhost:8080/callback'
            },
            'youtube': {
                'api_key': '',
                'client_id': '',
                'client_secret': ''
            },
            'bluetooth': {
                'device_name': 'Smart Shower',
                'pin_code': '0000'
            },
            'mobile': {
                'auth_secret': '',
                'push_notifications': {
                    'enabled': False,
                    'fcm_server_key': ''
                }
            }
        }
        
        self.credentials = default_credentials
        self._save_credentials()
        self.logger.info("Created default credentials file")
    
    def _create_default_configuration(self):
        """Create default configuration when loading fails"""
        self._create_default_settings()
        self._create_default_credentials()
    
    def _save_settings(self):
        """Save settings to file"""
        try:
            with open(self.settings_file, 'w') as f:
                yaml.dump(self.settings, f, default_flow_style=False, indent=2)
        except Exception as e:
            self.logger.error(f"Error saving settings: {e}")
    
    def _save_credentials(self):
        """Save credentials to file"""
        try:
            with open(self.credentials_file, 'w') as f:
                yaml.dump(self.credentials, f, default_flow_style=False, indent=2)
        except Exception as e:
            self.logger.error(f"Error saving credentials: {e}")
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value using dot notation"""
        keys = key.split('.')
        value = self.settings
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        
        return value
    
    def get_credential(self, key: str, default: Any = None) -> Any:
        """Get credential value using dot notation"""
        keys = key.split('.')
        value = self.credentials
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        
        return value
    
    def set(self, key: str, value: Any):
        """Set configuration value using dot notation"""
        keys = key.split('.')
        config = self.settings
        
        # Navigate to the parent of the target key
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        
        # Set the value
        config[keys[-1]] = value
        self._save_settings()
    
    def set_credential(self, key: str, value: Any):
        """Set credential value using dot notation"""
        keys = key.split('.')
        config = self.credentials
        
        # Navigate to the parent of the target key
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        
        # Set the value
        config[keys[-1]] = value
        self._save_credentials()
    
    def reload(self):
        """Reload configuration from files"""
        self.logger.info("Reloading configuration...")
        self._load_configuration()
    
    def get_all_settings(self) -> Dict[str, Any]:
        """Get all settings"""
        return self.settings.copy()
    
    def get_all_credentials(self) -> Dict[str, Any]:
        """Get all credentials"""
        return self.credentials.copy()
    
    def validate_configuration(self) -> bool:
        """Validate configuration"""
        errors = []
        
        # Check required settings
        required_settings = [
            'system.name',
            'water_control.default_temperature',
            'audio.default_volume',
            'safety.door_timeout'
        ]
        
        for setting in required_settings:
            if self.get(setting) is None:
                errors.append(f"Missing required setting: {setting}")
        
        # Check required credentials (optional for simulation mode)
        if not self.get('hardware.simulation_mode', True):
            required_credentials = [
                'spotify.client_id',
                'spotify.client_secret'
            ]
            
            for credential in required_credentials:
                if not self.get_credential(credential):
                    errors.append(f"Missing required credential: {credential}")
        
        if errors:
            for error in errors:
                self.logger.warning(error)
            return False
        
        self.logger.info("Configuration validation passed")
        return True
    
    def export_configuration(self, file_path: str):
        """Export configuration to file"""
        try:
            config_data = {
                'settings': self.settings,
                'credentials': self.credentials
            }
            
            with open(file_path, 'w') as f:
                yaml.dump(config_data, f, default_flow_style=False, indent=2)
            
            self.logger.info(f"Configuration exported to {file_path}")
            
        except Exception as e:
            self.logger.error(f"Error exporting configuration: {e}")
    
    def import_configuration(self, file_path: str):
        """Import configuration from file"""
        try:
            with open(file_path, 'r') as f:
                config_data = yaml.safe_load(f)
            
            if 'settings' in config_data:
                self.settings.update(config_data['settings'])
                self._save_settings()
            
            if 'credentials' in config_data:
                self.credentials.update(config_data['credentials'])
                self._save_credentials()
            
            self.logger.info(f"Configuration imported from {file_path}")
            
        except Exception as e:
            self.logger.error(f"Error importing configuration: {e}")
    
    def reset_to_defaults(self):
        """Reset configuration to defaults"""
        self.logger.info("Resetting configuration to defaults...")
        self._create_default_settings()
        self._create_default_credentials()
    
    def get_system_info(self) -> Dict[str, Any]:
        """Get system information"""
        return {
            'name': self.get('system.name', 'Smart Shower OS'),
            'version': self.get('system.version', '1.0.0'),
            'debug': self.get('system.debug', False),
            'log_level': self.get('system.log_level', 'INFO'),
            'simulation_mode': self.get('hardware.simulation_mode', True)
        }
    
    def is_simulation_mode(self) -> bool:
        """Check if system is in simulation mode"""
        return self.get('hardware.simulation_mode', True)
    
    def get_api_config(self) -> Dict[str, Any]:
        """Get API configuration"""
        return {
            'host': self.get('mobile_api.host', '0.0.0.0'),
            'port': self.get('mobile_api.port', 8080),
            'websocket_port': self.get('mobile_api.websocket_port', 8081),
            'session_timeout': self.get('mobile_api.session_timeout', 3600),
            'cors_enabled': self.get('mobile_api.cors_enabled', True)
        }
    
    def get_audio_config(self) -> Dict[str, Any]:
        """Get audio configuration"""
        return {
            'default_volume': self.get('audio.default_volume', 50),
            'audio_device': self.get('audio.audio_device', 'default'),
            'audio_format': self.get('audio.audio_format', 'mp3'),
            'sample_rate': self.get('audio.sample_rate', 44100),
            'local_music_path': self.get('audio.local_music_path', './music'),
            'bluetooth_enabled': self.get('audio.bluetooth_enabled', True)
        }
    
    def get_water_config(self) -> Dict[str, Any]:
        """Get water control configuration"""
        return {
            'default_temperature': self.get('water_control.default_temperature', 38.0),
            'max_temperature': self.get('water_control.max_temperature', 45.0),
            'min_temperature': self.get('water_control.min_temperature', 20.0),
            'default_flow_rate': self.get('water_control.default_flow_rate', 8.0),
            'max_flow_rate': self.get('water_control.max_flow_rate', 15.0),
            'pressure_limit': self.get('water_control.pressure_limit', 5.0)
        }
    
    def get_safety_config(self) -> Dict[str, Any]:
        """Get safety configuration"""
        return {
            'door_timeout': self.get('safety.door_timeout', 600),
            'max_shower_duration': self.get('safety.max_shower_duration', 1800),
            'leak_threshold': self.get('safety.leak_threshold', 0.1),
            'temperature_limit': self.get('safety.temperature_limit', 45.0),
            'emergency_stop_enabled': self.get('safety.emergency_stop_enabled', True)
        } 