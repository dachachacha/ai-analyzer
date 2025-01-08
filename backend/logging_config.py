# logging_config.py

from loguru import logger
import sys
import os

def setup_logging():
    logger.remove()  # Remove default handlers

    # Check for debug mode from the environment variable
    DEBUG_MODE = os.getenv("DEBUG", "false").lower() == "true"

    # Configure log level based on debug mode
    log_level = "DEBUG" if DEBUG_MODE else "INFO"
    #log_level = "DEBUG" if DEBUG_MODE else "DEBUG"
    
    # Add a logging sink
    logger.add(
        sys.stderr, 
        format="{time} {level} {message}", 
        level=log_level
    )

    logger.info(f"Logging initialized. Debug mode is {'ON' if DEBUG_MODE else 'OFF'}.")

