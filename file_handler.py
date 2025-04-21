"""
File Handler Module

This module handles loading and processing email files from the filesystem.
It provides functions to read .eml files and filter them by date range.
"""

import os
import datetime
import logging
from pathlib import Path
from email_parser import extract_email_date, extract_email_text

logger = logging.getLogger(__name__)

def get_emails_in_timeframe(folder_path, start_date, end_date):
    """
    Get all emails in the specified folder within the given timeframe.
    
    Args:
        folder_path (str or Path): Path to the folder containing .eml files
        start_date (datetime): Start date for filtering emails
        end_date (datetime): End date for filtering emails
        
    Returns:
        list: List of dictionaries containing date, text, and filename of filtered emails
    """
    email_texts = []
    folder_path = Path(folder_path)
    
    logger.info(f"Searching for .eml files in {folder_path}")
    eml_files = [f for f in os.listdir(folder_path) if f.endswith('.eml')]
    logger.info(f"Found {len(eml_files)} .eml files in folder")
    
    for file_name in eml_files:
        file_path = os.path.join(folder_path, file_name)
        logger.debug(f"Processing file: {file_name}")
        
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as file:
                email_content = file.read()
                
            # Extract the date and check if it's within the timeframe
            email_date = extract_email_date(email_content)
            if email_date and start_date <= email_date <= end_date:
                logger.debug(f"Email date {email_date} is within specified timeframe")
                email_texts.append({
                    'date': email_date, 
                    'text': extract_email_text(email_content), 
                    'file': file_name
                })
            else:
                logger.debug(f"Email date {email_date} is outside specified timeframe")
                
        except Exception as e:
            logger.error(f"Error processing {file_name}: {str(e)}")
    
    # Sort emails by date
    email_texts = sorted(email_texts, key=lambda x: x['date'])
    logger.info(f"Found {len(email_texts)} emails within the specified date range")
    
    return email_texts
