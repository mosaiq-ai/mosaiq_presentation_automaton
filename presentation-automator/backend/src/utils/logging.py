"""
Logging configuration for the application.
Sets up loggers with appropriate formatting and log levels.
"""

import sys
import logging
from pathlib import Path
from logging.handlers import RotatingFileHandler

from ..config.settings import get_settings

# Get settings
settings = get_settings()

# Define log format
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

# Define log levels
LOG_LEVELS = {
    "DEBUG": logging.DEBUG,
    "INFO": logging.INFO,
    "WARNING": logging.WARNING,
    "ERROR": logging.ERROR,
    "CRITICAL": logging.CRITICAL,
}


def setup_logger(name: str) -> logging.Logger:
    """
    Set up a logger with the specified name.
    
    Args:
        name: The name for the logger.
        
    Returns:
        A configured logger instance.
    """
    # Create logger
    logger = logging.getLogger(name)
    
    # Set log level from settings
    log_level = LOG_LEVELS.get(settings.server.log_level.upper(), logging.INFO)
    logger.setLevel(log_level)
    
    # Create handlers
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    
    # Create formatters
    formatter = logging.Formatter(LOG_FORMAT, datefmt=DATE_FORMAT)
    
    # Add formatters to handlers
    console_handler.setFormatter(formatter)
    
    # Add handlers to logger
    if not logger.handlers:
        logger.addHandler(console_handler)
    
    # Don't propagate to root logger
    logger.propagate = False
    
    return logger


# Create application logger
app_logger = setup_logger("presentation_automator") 