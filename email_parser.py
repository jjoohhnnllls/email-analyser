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

def extract_sender(email_content):
    """
    Extract the sender (From) from an email message.
    
    Args:
        email_content (str): The raw email content as a string
        
    Returns:
        tuple: (display_name, email_address) for the sender
    """
    logger.debug("Extracting sender (From) from email content")
    msg = email.message_from_string(email_content)
    sender = msg.get('From', '')
    
    # Parse the sender to extract both name and email
    if '<' in sender and '>' in sender:
        # Format like: "John Doe <john@example.com>"
        display_name = sender.split('<')[0].strip()
        email_address = sender.split('<')[1].split('>')[0].strip()
        return (display_name, email_address)
    else:
        # Just an email address with no name
        return ('', sender.strip())

def extract_recipients(email_content):
    """
    Extract all recipients (To and CC) from an email message.
    
    Args:
        email_content (str): The raw email content as a string
        
    Returns:
        list: List of (display_name, email_address) tuples for recipients
    """
    logger.debug("Extracting recipients (To, CC) from email content")
    msg = email.message_from_string(email_content)
    
    # Get To and CC fields
    to_field = msg.get('To', '')
    cc_field = msg.get('Cc', '') or msg.get('CC', '')  # Try both capitalizations
    
    # Combine and split recipients
    all_recipients = []
    
    # Process To field
    if to_field:
        # Split multiple recipients (separated by commas)
        to_recipients = [r.strip() for r in to_field.split(',')]
        all_recipients.extend(to_recipients)
    
    # Process CC field
    if cc_field:
        # Split multiple recipients (separated by commas)
        cc_recipients = [r.strip() for r in cc_field.split(',')]
        all_recipients.extend(cc_recipients)
    
    # Parse each recipient to extract both name and email
    parsed_recipients = []
    for recipient in all_recipients:
        if recipient:  # Skip empty recipients
            if '<' in recipient and '>' in recipient:
                display_name = recipient.split('<')[0].strip()
                email_address = recipient.split('<')[1].split('>')[0].strip()
                parsed_recipients.append((display_name, email_address))
            else:
                # Just an email address with no name
                parsed_recipients.append(('', recipient.strip()))
    
    return parsed_recipients