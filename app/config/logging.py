import logging
import sys
import os

def configure_logging(log_level=None):
    """Configure logging for the entire application"""
    if log_level is None:
        log_level = os.getenv("LOG_LEVEL", "INFO")
    
    # Convert string to logging level
    numeric_level = getattr(logging, log_level.upper(), None)
    if not isinstance(numeric_level, int):
        numeric_level = logging.INFO
    
    # Configure the root logger
    logging.basicConfig(
        level=numeric_level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)]
    )
    
    # Silence some verbose third-party loggers if needed
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("paho.mqtt").setLevel(logging.WARNING)