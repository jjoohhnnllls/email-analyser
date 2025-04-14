import os
import email
import datetime
from dateutil import parser
import argparse
from pathlib import Path
import ollama
import textwrap
import sys 
import time

def extract_email_date(email_content):
    """Extract the date from an email message."""
    msg = email.message_from_string(email_content)
    date_str = msg.get('Date')
    if date_str:
        try:
            # Convert to offset-naive datetime by replacing timezone info
            dt = parser.parse(date_str)
            return dt.replace(tzinfo=None)
        except:
            return None
    return None

def extract_email_text(email_content):
    """Extract text content from an email message."""
    msg = email.message_from_string(email_content)
    
    # Initialize an empty string to store the email text
    email_text = ""
    
    # Extract subject
    subject = msg.get('Subject', '')
    email_text += f"Subject: {subject}\n\n"
    
    # Extract sender
    sender = msg.get('From', '')
    email_text += f"From: {sender}\n\n"
    
    # Extract body
    if msg.is_multipart():
        for part in msg.walk():
            content_type = part.get_content_type()
            content_disposition = str(part.get('Content-Disposition'))
            
            # Skip attachments
            if 'attachment' in content_disposition:
                continue
            
            # Get the body of the email
            if content_type == 'text/plain':
                try:
                    payload = part.get_payload(decode=True).decode('utf-8', errors='ignore')
                    email_text += payload
                except:
                    pass
    else:
        # If the email is not multipart, just get the payload
        try:
            payload = msg.get_payload(decode=True).decode('utf-8', errors='ignore')
            email_text += payload
        except:
            pass
    
    return email_text

def get_emails_in_timeframe(folder_path, start_date, end_date):
    """Get all emails in the specified folder within the given timeframe."""
    email_texts = []
    
    # Get all .eml files in the folder
    eml_files = [f for f in os.listdir(folder_path) if f.endswith('.eml')]
    
    print(f"Found {len(eml_files)} .eml files in folder. Processing...")
    
    for file_name in eml_files:
        file_path = os.path.join(folder_path, file_name)
        
        # Read the email content
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as file:
                email_content = file.read()
            
            # Extract date from email
            email_date = extract_email_date(email_content)
            
            # Check if the email is within the specified timeframe
            if email_date and start_date <= email_date <= end_date:
                email_text = extract_email_text(email_content)
                email_texts.append({
                    'date': email_date,
                    'text': email_text,
                    'file': file_name
                })
        except Exception as e:
            print(f"Error processing {file_name}: {str(e)}")
    
    # Sort emails by date
    email_texts.sort(key=lambda x: x['date'])
    
    return email_texts

def prepare_email_summary(email_texts, max_chars=1000):
    """Prepare a summary of emails for the LLM."""
    total_emails = len(email_texts)
    summary = []
    
    # Add metadata summary
    date_range = ""
    if total_emails > 0:
        first_date = email_texts[0]['date'].strftime('%Y-%m-%d')
        last_date = email_texts[-1]['date'].strftime('%Y-%m-%d')
        date_range = f"from {first_date} to {last_date}"
    
    summary.append(f"TOTAL EMAILS: {total_emails} {date_range}")
    
    # Group emails by sender domain for a quick overview
    sender_domains = {}
    subjects = []
    
    for email_data in email_texts:
        # Extract sender domain
        text = email_data['text']
        from_line = next((line for line in text.split('\n') if line.startswith('From:')), "")
        
        if '@' in from_line:
            domain = from_line.split('@')[1].split()[0].strip()
            sender_domains[domain] = sender_domains.get(domain, 0) + 1
        
        # Extract subject
        subject_line = next((line for line in text.split('\n') if line.startswith('Subject:')), "")
        if subject_line:
            subjects.append(subject_line[9:].strip())  # Remove "Subject: " prefix
    
    # Add domain summary
    summary.append("\nSENDER DOMAINS:")
    for domain, count in sorted(sender_domains.items(), key=lambda x: x[1], reverse=True)[:10]:
        summary.append(f"- {domain}: {count} emails")
    
    # Add subject samples
    summary.append("\nSAMPLE SUBJECTS:")
    for subject in subjects[:10]:
        if subject:
            summary.append(f"- {subject}")
    
    # Add email content samples
    summary.append("\nEMAIL SAMPLES:")
    
    # Select a representative sample of emails (first, middle, last, and some random ones)
    sample_indices = [0]
    if total_emails > 1:
        sample_indices.append(total_emails - 1)
    if total_emails > 2:
        sample_indices.append(total_emails // 2)
    
    # Add some samples spread throughout the dataset
    step = max(1, total_emails // 10)
    for i in range(step, total_emails, step):
        if i not in sample_indices:
            sample_indices.append(i)
            if len(sample_indices) >= 10:  # Limit to 10 samples
                break
    
    # Sort indices to maintain chronological order
    sample_indices.sort()
    
    # Add sample content
    for idx in sample_indices:
        if idx < len(email_texts):
            email_data = email_texts[idx]
            date_str = email_data['date'].strftime('%Y-%m-%d %H:%M')
            
            # Extract just the first few lines of text
            text_lines = email_data['text'].split('\n')
            preview = '\n'.join(text_lines[:10])  # First 10 lines
            if len(text_lines) > 10:
                preview += "\n[...]"  # Indicate there's more content
            
            summary.append(f"\nEMAIL {idx+1}/{total_emails} (Date: {date_str}):")
            summary.append(textwrap.fill(preview, width=80))
    
    return "\n".join(summary)

def analyze_emails_with_ollama(email_texts):
    """Analyze email texts using Ollama's Mistral model."""
    
    # Prepare summary of all emails for context
    email_summary = prepare_email_summary(email_texts)
    
    # Prepare prompt for Ollama
    prompt = f"""You are analyzing a collection of {len(email_texts)} emails. 
I will provide you with an overview of these emails. Based on this information, please:

1. Give a brief overview and summary of what all of these emails appear to be about . make sure this information is useful for a digital forensics investigator
2. Identify any key patterns or trends in all of the emails
3. Note interesting insights or important content(give me as many insights as possible that maybe relevant to a forensics point of view)
4. Suggest any actions or follow-ups that might be 
5. note down any important dates, person , names , actions or any key insights. this information may be used for forensic analysis
6. you may include some other statistics as well like percentages etc, that will be of interest to a digital forensics investigator 
7. highlight anything that is unusual or noteworthy
Here is the email dataset overview:

{email_summary}

Please analyze this information and provide your insights. Be specific and highlight anything unusual or noteworthy


"""
    
    # Send to Ollama for analysis
    try:
        print("Sending data to Ollama for analysis...")
        print("\n===================== Email Analysis Results ==========================\n")
        stream = ollama.chat(
            model='mistral',
            messages=[{'role': 'user', 'content': prompt}],
            stream=True  # enable streaming
        )
        
        # Collect and print response in real-time
        full_response = ""
        for chunk in stream: 
            if 'message' in chunk:
                print(chunk['message']['content'], end='', flush=True)
                full_response += chunk['message']['content']
        
        return full_response
    except Exception as e:
        return f"Error analyzing emails with Ollama: {str(e)}"

def main():
    # Set up argument parser
    parser = argparse.ArgumentParser(description='Analyze emails in a specified folder.')
    parser.add_argument('--folder', type=str, help='Path to folder containing .eml files')
    args = parser.parse_args()
    
    # Ask for folder path if not provided
    folder_path = args.folder
    if not folder_path:
        folder_path = input("Enter the path to the folder containing .eml files: ")
    
    # Validate folder path
    folder_path = Path(folder_path)
    if not folder_path.exists() or not folder_path.is_dir():
        print(f"Error: The folder '{folder_path}' does not exist or is not a directory.")
        return
    
    # Ask for date range
    print("\nPlease specify the date range for emails to analyze.")
    start_date_str = input("Enter start date (YYYY-MM-DD): ")
    end_date_str = input("Enter end date (YYYY-MM-DD): ")
    
    try:
        start_date = datetime.datetime.strptime(start_date_str, "%Y-%m-%d")
        end_date = datetime.datetime.strptime(end_date_str, "%Y-%m-%d")
        # Set end date to the end of the day
        end_date = end_date.replace(hour=23, minute=59, second=59)
    except ValueError:
        print("Error: Invalid date format. Please use YYYY-MM-DD.")
        return
    
    # Get emails in the specified timeframe
    print(f"\nFetching emails from {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}...")
    email_texts = get_emails_in_timeframe(folder_path, start_date, end_date)
    
    # Check if any emails were found
    if not email_texts:
        print("No emails found in the specified date range.")
        return
    
    print(f"Found {len(email_texts)} emails in the specified date range.")
    
    # Analyze emails with Ollama
    # Display results
    print("\nAnalyzing emails with Ollama's Mistral model...")
    
    analysis_result = analyze_emails_with_ollama(email_texts)
    print("\n=======================================================================\n")
    
if __name__ == "__main__":
    main()