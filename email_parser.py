"""
Email Parser Module

This module contains functions for extracting text and metadata from email messages.
It handles parsing email headers, extracting dates, and getting the text content.
"""

import email
from dateutil import parser
import logging

logger = logging.getLogger(__name__)

def extract_email_date(email_content):
    """
    Extract the date from an email message.
    
    Args:
        email_content (str): The raw email content as a string
        
    Returns:
        datetime or None: The parsed date, with timezone info removed, or None if date can't be parsed
    """
    logger.debug("Extracting date from email")
    msg = email.message_from_string(email_content)
    date_str = msg.get('Date')
    if date_str:
        try:
            dt = parser.parse(date_str)
            return dt.replace(tzinfo=None)
        except Exception as e:
            logger.warning(f"Failed to parse email date: {e}")
            return None
    logger.debug("No date found in email")
    return None

def extract_email_text(email_content):
    """
    Extract text content from an email message including subject and sender.
    
    Args:
        email_content (str): The raw email content as a string
        
    Returns:
        str: The extracted email text including Subject and From fields
    """
    logger.debug("Extracting text content from email")
    msg = email.message_from_string(email_content)
    email_text = f"Subject: {msg.get('Subject', '')}\n\nFrom: {msg.get('From', '')}\n\n"
    
    # Handle multipart email messages
    if msg.is_multipart():
        logger.debug("Processing multipart email")
        for part in msg.walk():
            content_type = part.get_content_type()
            content_disposition = str(part.get('Content-Disposition'))
            
            # Skip attachments
            if 'attachment' in content_disposition:
                continue
                
            if content_type == 'text/plain':
                try:
                    email_text += part.get_payload(decode=True).decode('utf-8', errors='ignore')
                except Exception as e:
                    logger.warning(f"Error decoding email part: {e}")
    else:
        # Handle single part email messages
        logger.debug("Processing single part email")
        try:
            email_text += msg.get_payload(decode=True).decode('utf-8', errors='ignore')
        except Exception as e:
            logger.warning(f"Error decoding email payload: {e}")
    
    return email_text
