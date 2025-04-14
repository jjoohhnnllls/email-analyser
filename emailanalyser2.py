import os
import sys
import time
import email
import datetime
from dateutil import parser
import argparse
from pathlib import Path
import ollama
import textwrap

def extract_email_date(email_content):
    """Extract the date from an email message."""
    msg = email.message_from_string(email_content)
    date_str = msg.get('Date')
    if date_str:
        try:
            dt = parser.parse(date_str)
            return dt.replace(tzinfo=None)
        except:
            return None
    return None

def extract_email_text(email_content):
    """Extract text content from an email message."""
    msg = email.message_from_string(email_content)
    email_text = f"Subject: {msg.get('Subject', '')}\n\nFrom: {msg.get('From', '')}\n\n"
    
    if msg.is_multipart():
        for part in msg.walk():
            content_type = part.get_content_type()
            content_disposition = str(part.get('Content-Disposition'))
            if 'attachment' in content_disposition:
                continue
            if content_type == 'text/plain':
                try:
                    email_text += part.get_payload(decode=True).decode('utf-8', errors='ignore')
                except:
                    pass
    else:
        try:
            email_text += msg.get_payload(decode=True).decode('utf-8', errors='ignore')
        except:
            pass
    
    return email_text

def get_emails_in_timeframe(folder_path, start_date, end_date):
    """Get all emails in the specified folder within the given timeframe."""
    email_texts = []
    eml_files = [f for f in os.listdir(folder_path) if f.endswith('.eml')]
    print(f"Found {len(eml_files)} .eml files in folder. Processing...")
    
    for file_name in eml_files:
        file_path = os.path.join(folder_path, file_name)
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as file:
                email_content = file.read()
            email_date = extract_email_date(email_content)
            if email_date and start_date <= email_date <= end_date:
                email_texts.append({'date': email_date, 'text': extract_email_text(email_content), 'file': file_name})
        except Exception as e:
            print(f"Error processing {file_name}: {str(e)}")
    
    return sorted(email_texts, key=lambda x: x['date'])

def prepare_email_summary(email_texts):
    """Prepare a summary of emails for the LLM."""
    total_emails = len(email_texts)
    summary = [f"TOTAL EMAILS: {total_emails} ({email_texts[0]['date'].strftime('%Y-%m-%d')} to {email_texts[-1]['date'].strftime('%Y-%m-%d')})" if total_emails else "TOTAL EMAILS: 0"]
    
    sender_domains = {}
    subjects = []
    
    for email_data in email_texts:
        from_line = next((line for line in email_data['text'].split('\n') if line.startswith('From:')), "")
        if '@' in from_line:
            domain = from_line.split('@')[1].split()[0].strip()
            sender_domains[domain] = sender_domains.get(domain, 0) + 1
        subject_line = next((line for line in email_data['text'].split('\n') if line.startswith('Subject:')), "")
        if subject_line:
            subjects.append(subject_line[9:].strip())
    
    summary.append("\nSENDER DOMAINS:")
    summary.extend([f"- {domain}: {count} emails" for domain, count in sorted(sender_domains.items(), key=lambda x: x[1], reverse=True)[:10]])
    
    summary.append("\nSAMPLE SUBJECTS:")
    summary.extend([f"- {subject}" for subject in subjects[:10] if subject])
    
    return "\n".join(summary)

def analyze_emails_with_ollama(email_texts):
    """Analyze email texts using Ollama's Mistral model and stream output."""
    email_summary = prepare_email_summary(email_texts)
    prompt = f"""you are analyzing a collection of {len(email_texts)} emails. \n
Here is the email dataset overview:\n\n{email_summary}\n
Please analyze this information and provide your insights. Be specific and highlight anything unusual or noteworthy."""
    
    try:
        print("Sending data to Ollama for analysis...\n")
        response = ollama.chat(
            model='mistral',
            messages=[{'role': 'user', 'content': prompt}],
            stream=True
        )
        print("\n======== Email Analysis Results ========\n")
        
        for chunk in response:
            sys.stdout.write(chunk['message']['content'])
            sys.stdout.flush()
        
        print("\n======================================\n")
    except Exception as e:
        print(f"Error analyzing emails with Ollama: {str(e)}")

def main():
    parser = argparse.ArgumentParser(description='Analyze emails in a specified folder.')
    parser.add_argument('--folder', type=str, help='Path to folder containing .eml files')
    args = parser.parse_args()
    
    folder_path = args.folder or input("Enter the path to the folder containing .eml files: ")
    folder_path = Path(folder_path)
    if not folder_path.exists() or not folder_path.is_dir():
        print(f"Error: The folder '{folder_path}' does not exist or is not a directory.")
        return
    
    print("\nPlease specify the date range for emails to analyze.")
    try:
        start_date = datetime.datetime.strptime(input("Enter start date (YYYY-MM-DD): "), "%Y-%m-%d")
        end_date = datetime.datetime.strptime(input("Enter end date (YYYY-MM-DD): "), "%Y-%m-%d").replace(hour=23, minute=59, second=59)
    except ValueError:
        print("Error: Invalid date format. Please use YYYY-MM-DD.")
        return
    
    print(f"\nFetching emails from {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}...")
    email_texts = get_emails_in_timeframe(folder_path, start_date, end_date)
    
    if not email_texts:
        print("No emails found in the specified date range.")
        return
    
    print(f"Found {len(email_texts)} emails in the specified date range.")
    print("\nAnalyzing emails with large lanaguage model...\n")
    analyze_emails_with_ollama(email_texts)

if __name__ == "__main__":
    main()
