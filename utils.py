"""
Utils Module

This module contains utility functions for the application,
including logging setup and any other helper functions.
"""

import logging
import os
from datetime import datetime

def setup_logging(log_dir="logs"):
    """
    Set up logging configuration for the application.
    
    Args:
        log_dir (str): Directory to store log files
        
    Returns:
        logging.Logger: Configured logger object
    """
    # Create logs directory if it doesn't exist
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    
    # Create a unique log filename with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_filename = os.path.join(log_dir, f"email_analyzer_{timestamp}.log")
    
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_filename),
            logging.StreamHandler()  # Also output to console
        ]
    )
    
    logger = logging.getLogger("email_analyzer")
    logger.info(f"Logging initialized. Log file: {log_filename}")
    
    return logger