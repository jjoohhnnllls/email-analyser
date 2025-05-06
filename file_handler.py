"""
File Handler Module

This module handles loading and processing email files from the filesystem.
It provides functions to read .eml files and filter them by date range.
"""

import os
import datetime
import logging
from pathlib import Path
from email_parser import extract_email_date, extract_email_text, extract_sender, extract_recipients
import email

logger = logging.getLogger(__name__)

def get_emails_in_timeframe(folder_path, start_date, end_date):
    """
    Get all emails within the specified date range.
    
    Args:
        folder_path (str): Path to folder containing .eml files
        start_date (datetime.date): Start date for filtering
        end_date (datetime.date): End date for filtering
        
    Returns:
        list: List of email texts within the date range
    """
    logger = logging.getLogger('file_handler')
    logger.info(f"Searching for .eml files in {folder_path}")
    
    # Get all .eml files
    eml_files = [f for f in os.listdir(folder_path) if f.endswith('.eml')]
    logger.info(f"Found {len(eml_files)} .eml files in folder")
    
    # Convert end_date to datetime at end of day with UTC timezone
    if isinstance(end_date, datetime.date):
        end_date = datetime.datetime.combine(end_date, datetime.time(23, 59, 59))
        end_date = end_date.replace(tzinfo=datetime.timezone.utc)
    
    # Convert start_date to datetime at start of day with UTC timezone
    if isinstance(start_date, datetime.date):
        start_date = datetime.datetime.combine(start_date, datetime.time(0, 0, 0))
        start_date = start_date.replace(tzinfo=datetime.timezone.utc)
    
    email_texts = []
    for file in eml_files:
        try:
            file_path = os.path.join(folder_path, file)
            with open(file_path, 'r', encoding='utf-8') as f:
                email_content = f.read()
                
            # Parse email date
            msg = email.message_from_string(email_content)
            date_str = msg.get('date')
            if date_str:
                try:
                    # Parse the date string and ensure it's timezone-aware
                    email_date = email.utils.parsedate_to_datetime(date_str)
                    if email_date.tzinfo is None:
                        # If the email date is naive (no timezone), assume UTC
                        email_date = email_date.replace(tzinfo=datetime.timezone.utc)
                    
                    # Check if email is within date range
                    if start_date <= email_date <= end_date:
                        email_texts.append(email_content)
                except Exception as e:
                    logger.error(f"Error parsing date in {file}: {str(e)}")
            else:
                logger.warning(f"No date found in {file}")
                
        except Exception as e:
            logger.error(f"Error processing {file}: {str(e)}")
    
    logger.info(f"Found {len(email_texts)} emails within the specified date range")
    return email_texts

def get_raw_email_contents(email_texts):
    """
    Extract raw email content from a list of email texts.
    
    Args:
        email_texts (list): List of email content strings
        
    Returns:
        list: List of raw email content strings
    """
    # Since email_texts is already a list of raw email content strings,
    # we can return it directly
    return email_texts