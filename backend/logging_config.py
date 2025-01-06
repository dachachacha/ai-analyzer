# logging_config.py

from loguru import logger
import sys

def setup_logging():
    logger.remove()  # Remove default handlers
    logger.add(sys.stderr, format="{time} {level} {message}", level="INFO")

