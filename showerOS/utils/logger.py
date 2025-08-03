"""
Logger utility for Smart Shower OS
Sets up logging configuration
"""

import logging
import logging.handlers
import os
import sys
from pathlib import Path
from typing import Optional


def setup_logging(
    log_level: str = "INFO",
    log_file: str = "./logs/shower.log",
    max_size: int = 10485760,  # 10MB
    backup_count: int = 5,
    console_output: bool = True
):
    """Set up logging configuration"""
    
    # Create logs directory if it doesn't exist
    log_path = Path(log_file)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Configure logging level
    level = getattr(logging, log_level.upper(), logging.INFO)
    
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Clear existing handlers
    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    root_logger.setLevel(level)
    
    # File handler with rotation
    file_handler = logging.handlers.RotatingFileHandler(
        log_file,
        maxBytes=max_size,
        backupCount=backup_count,
        encoding='utf-8'
    )
    file_handler.setLevel(level)
    file_handler.setFormatter(formatter)
    root_logger.addHandler(file_handler)
    
    # Console handler
    if console_output:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(level)
        console_handler.setFormatter(formatter)
        root_logger.addHandler(console_handler)
    
    # Set specific logger levels
    logging.getLogger('aiohttp').setLevel(logging.WARNING)
    logging.getLogger('asyncio').setLevel(logging.WARNING)
    
    # Log startup message
    logger = logging.getLogger(__name__)
    logger.info(f"Logging initialized - Level: {log_level}, File: {log_file}")


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance"""
    return logging.getLogger(name)


def set_log_level(level: str):
    """Set the logging level"""
    level_upper = level.upper()
    if hasattr(logging, level_upper):
        logging.getLogger().setLevel(getattr(logging, level_upper))
        logger = logging.getLogger(__name__)
        logger.info(f"Log level changed to {level_upper}")
    else:
        logger = logging.getLogger(__name__)
        logger.warning(f"Invalid log level: {level}")


def add_file_handler(log_file: str, level: str = "INFO"):
    """Add a file handler to the root logger"""
    log_path = Path(log_file)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setLevel(getattr(logging, level.upper(), logging.INFO))
    file_handler.setFormatter(formatter)
    
    logging.getLogger().addHandler(file_handler)
    
    logger = logging.getLogger(__name__)
    logger.info(f"Added file handler: {log_file}")


def add_rotating_file_handler(
    log_file: str,
    max_size: int = 10485760,  # 10MB
    backup_count: int = 5,
    level: str = "INFO"
):
    """Add a rotating file handler to the root logger"""
    log_path = Path(log_file)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    file_handler = logging.handlers.RotatingFileHandler(
        log_file,
        maxBytes=max_size,
        backupCount=backup_count,
        encoding='utf-8'
    )
    file_handler.setLevel(getattr(logging, level.upper(), logging.INFO))
    file_handler.setFormatter(formatter)
    
    logging.getLogger().addHandler(file_handler)
    
    logger = logging.getLogger(__name__)
    logger.info(f"Added rotating file handler: {log_file}")


class LoggerMixin:
    """Mixin class to add logging functionality"""
    
    @property
    def logger(self) -> logging.Logger:
        """Get logger for this class"""
        return logging.getLogger(self.__class__.__name__)


def log_function_call(func):
    """Decorator to log function calls"""
    def wrapper(*args, **kwargs):
        logger = logging.getLogger(func.__module__)
        logger.debug(f"Calling {func.__name__} with args={args}, kwargs={kwargs}")
        try:
            result = func(*args, **kwargs)
            logger.debug(f"{func.__name__} returned {result}")
            return result
        except Exception as e:
            logger.error(f"{func.__name__} raised {type(e).__name__}: {e}")
            raise
    return wrapper


def log_async_function_call(func):
    """Decorator to log async function calls"""
    async def wrapper(*args, **kwargs):
        logger = logging.getLogger(func.__module__)
        logger.debug(f"Calling async {func.__name__} with args={args}, kwargs={kwargs}")
        try:
            result = await func(*args, **kwargs)
            logger.debug(f"Async {func.__name__} returned {result}")
            return result
        except Exception as e:
            logger.error(f"Async {func.__name__} raised {type(e).__name__}: {e}")
            raise
    return wrapper


class StructuredLogger:
    """Structured logger for JSON-formatted logs"""
    
    def __init__(self, name: str):
        self.logger = logging.getLogger(name)
    
    def info(self, message: str, **kwargs):
        """Log info message with structured data"""
        self.logger.info(f"{message} | {kwargs}")
    
    def warning(self, message: str, **kwargs):
        """Log warning message with structured data"""
        self.logger.warning(f"{message} | {kwargs}")
    
    def error(self, message: str, **kwargs):
        """Log error message with structured data"""
        self.logger.error(f"{message} | {kwargs}")
    
    def debug(self, message: str, **kwargs):
        """Log debug message with structured data"""
        self.logger.debug(f"{message} | {kwargs}")


def setup_structured_logging(
    log_file: str = "./logs/structured.log",
    level: str = "INFO"
):
    """Set up structured logging"""
    log_path = Path(log_file)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Create structured logger
    structured_logger = logging.getLogger('structured')
    structured_logger.setLevel(getattr(logging, level.upper(), logging.INFO))
    
    # File handler for structured logs
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setLevel(getattr(logging, level.upper(), logging.INFO))
    
    # JSON formatter
    class JSONFormatter(logging.Formatter):
        def format(self, record):
            import json
            log_entry = {
                'timestamp': self.formatTime(record),
                'level': record.levelname,
                'logger': record.name,
                'message': record.getMessage(),
                'module': record.module,
                'function': record.funcName,
                'line': record.lineno
            }
            return json.dumps(log_entry)
    
    file_handler.setFormatter(JSONFormatter())
    structured_logger.addHandler(file_handler)
    
    return structured_logger


def log_system_event(event_type: str, details: dict, level: str = "INFO"):
    """Log a system event"""
    logger = logging.getLogger('system_events')
    message = f"SYSTEM_EVENT: {event_type} | {details}"
    
    if level.upper() == "INFO":
        logger.info(message)
    elif level.upper() == "WARNING":
        logger.warning(message)
    elif level.upper() == "ERROR":
        logger.error(message)
    elif level.upper() == "DEBUG":
        logger.debug(message)


def log_water_event(event_type: str, temperature: float = None, flow_rate: float = None):
    """Log a water control event"""
    details = {}
    if temperature is not None:
        details['temperature'] = temperature
    if flow_rate is not None:
        details['flow_rate'] = flow_rate
    
    log_system_event(f"WATER_{event_type.upper()}", details)


def log_audio_event(event_type: str, source: str = None, track: str = None):
    """Log an audio event"""
    details = {}
    if source is not None:
        details['source'] = source
    if track is not None:
        details['track'] = track
    
    log_system_event(f"AUDIO_{event_type.upper()}", details)


def log_safety_event(event_type: str, details: dict = None):
    """Log a safety event"""
    if details is None:
        details = {}
    log_system_event(f"SAFETY_{event_type.upper()}", details, level="WARNING")


def log_mobile_event(event_type: str, device_id: str = None, details: dict = None):
    """Log a mobile API event"""
    if details is None:
        details = {}
    if device_id is not None:
        details['device_id'] = device_id
    
    log_system_event(f"MOBILE_{event_type.upper()}", details) 